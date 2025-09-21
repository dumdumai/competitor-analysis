from datetime import datetime
from typing import Dict, Any, List
from loguru import logger
from models.agent_state import AgentState
from models.reports import Report, ReportSection
from services.llm_service import LLMService


class ReportGenerationAgent:
    """Agent responsible for generating comprehensive analysis reports"""
    
    def __init__(self, llm_service: LLMService):
        self.name = "report_generation"
        self.llm_service = llm_service
    
    async def process(self, state: AgentState) -> AgentState:
        """Generate comprehensive analysis report"""
        try:
            logger.info(f"Starting report generation for {state.analysis_context.client_company}")
            
            # Update progress
            state.update_progress("report_generation", 40)
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(state)
            state.update_progress("report_generation", 50)
            
            # Generate report sections
            sections = await self._generate_report_sections(state)
            state.update_progress("report_generation", 80)
            
            # Create final report
            report = self._create_final_report(
                state, executive_summary, sections
            )
            
            # Store report
            state.processed_data["final_report"] = report.dict()
            
            # Update metadata
            state.metadata.update({
                "report_generated": True,
                "report_sections": len(sections),
                "executive_summary_length": len(executive_summary),
                "total_competitors_in_report": len(state.competitor_data)
            })
            
            # Complete the stage
            state.complete_stage("report_generation")
            state.update_progress("report_generation", 100)
            
            logger.info("Report generation completed successfully")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in report generation: {e}")
            state.add_error(f"Report generation failed: {str(e)}")
            return state
    
    async def _generate_executive_summary(self, state: AgentState) -> str:
        """Generate executive summary using LLM"""
        try:
            return await self.llm_service.generate_executive_summary(
                client_company=state.analysis_context.client_company,
                industry=state.analysis_context.industry,
                competitors=[comp.dict() for comp in state.competitor_data],
                market_analysis=state.market_insights,
                competitive_analysis=state.competitive_analysis
            )
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return self._create_fallback_executive_summary(state)
    
    def _create_fallback_executive_summary(self, state: AgentState) -> str:
        """Create fallback executive summary when LLM fails"""
        context = state.analysis_context
        num_competitors = len(state.competitor_data)
        
        return f"""
        Executive Summary
        
        This competitive analysis examines the market landscape for {context.client_company} 
        in the {context.industry} industry, focusing on the {context.target_market} market.
        
        Our analysis identified {num_competitors} key competitors and provides strategic 
        insights into market positioning, competitive threats, and growth opportunities.
        
        Key findings include market dynamics analysis, competitive positioning assessment, 
        and strategic recommendations for maintaining competitive advantage.
        
        The analysis reveals opportunities for differentiation and growth in specific 
        market segments while highlighting potential threats that require strategic attention.
        """
    
    async def _generate_report_sections(self, state: AgentState) -> Dict[str, ReportSection]:
        """Generate all report sections"""
        sections = {}
        
        # Market Overview Section
        sections["market_overview"] = self._create_market_overview_section(state)
        
        # Competitive Landscape Section
        sections["competitive_landscape"] = self._create_competitive_landscape_section(state)
        
        # Competitor Profiles Sections
        sections["competitor_profiles"] = self._create_competitor_profiles_sections(state)
        
        # SWOT Analysis Section
        sections["swot_analysis"] = self._create_swot_analysis_section(state)
        
        # Market Positioning Section
        sections["market_positioning"] = self._create_market_positioning_section(state)
        
        # Threats and Opportunities Section
        sections["threats_opportunities"] = self._create_threats_opportunities_section(state)
        
        # Strategic Recommendations Section
        sections["strategic_recommendations"] = self._create_strategic_recommendations_section(state)
        
        return sections
    
    def _create_market_overview_section(self, state: AgentState) -> ReportSection:
        """Create market overview section"""
        market_analysis = state.market_insights
        
        content = f"""
        Market Overview: {state.analysis_context.industry} Industry
        
        Industry: {state.analysis_context.industry}
        Target Market: {state.analysis_context.target_market}
        Analysis Date: {datetime.utcnow().strftime('%B %d, %Y')}
        
        Market Size and Growth:
        """
        
        if market_analysis and "market_size" in market_analysis:
            market_size = market_analysis["market_size"]
            content += f"""
            Current Market Size: {market_size.get('current_size', 'Not specified')}
            Growth Rate: {market_size.get('growth_rate', 'Not specified')}
            Market Forecast: {market_size.get('forecast', 'Not specified')}
            """
        
        # Add key trends
        if market_analysis and "key_trends" in market_analysis:
            trends = market_analysis["key_trends"]
            content += "\n\nKey Market Trends:\n"
            for i, trend in enumerate(trends[:5], 1):
                content += f"{i}. {trend}\n"
        
        # Add competitive intensity
        if market_analysis and "competitive_intensity" in market_analysis:
            content += f"\nCompetitive Intensity: {market_analysis['competitive_intensity']}"
        
        key_insights = [
            f"Analysis covers {len(state.competitor_data)} key competitors",
            f"Market shows {market_analysis.get('competitive_intensity', 'medium')} competitive intensity",
            "Multiple market segments identified for potential targeting"
        ]
        
        return ReportSection(
            title="Market Overview",
            content=content,
            key_insights=key_insights
        )
    
    def _create_competitive_landscape_section(self, state: AgentState) -> ReportSection:
        """Create competitive landscape section"""
        competitors = state.competitor_data
        
        content = f"""
        Competitive Landscape Analysis
        
        Total Competitors Analyzed: {len(competitors)}
        High-Quality Data Available: {len(state.get_high_quality_competitors())}
        
        Competitor Distribution by Business Model:
        """
        
        # Analyze business model distribution
        business_models = {}
        for comp in competitors:
            bm = getattr(comp, 'business_model', 'Unknown')
            business_models[bm] = business_models.get(bm, 0) + 1
        
        for bm, count in business_models.items():
            content += f"\n- {bm}: {count} competitors"
        
        # Add market positioning
        content += "\n\nMarket Positioning Analysis:\n"
        
        top_competitors = sorted(
            competitors, 
            key=lambda x: state.quality_scores.get(x.name, 0), 
            reverse=True
        )[:5]
        
        for i, comp in enumerate(top_competitors, 1):
            content += f"\n{i}. {comp.name}"
            if comp.market_position:
                content += f" - {comp.market_position}"
        
        key_insights = [
            f"Market dominated by {len([c for c in competitors if 'large' in str(getattr(c, 'employee_count', '')).lower()])} large players",
            f"Most common business model: {max(business_models.items(), key=lambda x: x[1])[0] if business_models else 'Unknown'}",
            "Significant opportunities for differentiation identified"
        ]
        
        return ReportSection(
            title="Competitive Landscape",
            content=content,
            key_insights=key_insights
        )
    
    def _create_competitor_profiles_sections(self, state: AgentState) -> List[ReportSection]:
        """Create individual competitor profile sections"""
        profiles = []
        
        # Get top competitors for detailed profiles
        top_competitors = sorted(
            state.competitor_data,
            key=lambda x: state.quality_scores.get(x.name, 0),
            reverse=True
        )[:8]  # Top 8 competitors
        
        for comp in top_competitors:
            profile_content = f"""
            Company Profile: {comp.name}
            
            Business Overview:
            {comp.description}
            
            Business Model: {comp.business_model}
            Target Market: {comp.target_market}
            """
            
            if comp.website:
                profile_content += f"\nWebsite: {comp.website}"
            
            if comp.founding_year:
                profile_content += f"\nFounded: {comp.founding_year}"
            
            if comp.headquarters:
                profile_content += f"\nHeadquarters: {comp.headquarters}"
            
            if comp.employee_count:
                profile_content += f"\nEmployee Count: {comp.employee_count}"
            
            # Add strengths and weaknesses
            if comp.strengths:
                profile_content += "\n\nKey Strengths:\n"
                for strength in comp.strengths[:5]:
                    profile_content += f"• {strength}\n"
            
            if comp.weaknesses:
                profile_content += "\nKey Weaknesses:\n"
                for weakness in comp.weaknesses[:3]:
                    profile_content += f"• {weakness}\n"
            
            # Add products
            if comp.key_products:
                profile_content += f"\nKey Products/Services: {', '.join(comp.key_products[:5])}"
            
            # Add competitive advantages
            if comp.competitive_advantages:
                profile_content += "\n\nCompetitive Advantages:\n"
                for advantage in comp.competitive_advantages[:3]:
                    profile_content += f"• {advantage}\n"
            
            threat_level = getattr(comp, 'threat_level', 'Medium')
            profile_content += f"\nThreat Level to Client: {threat_level}"
            
            key_insights = [
                f"Primary focus: {comp.business_model}",
                f"Market position: {comp.market_position or 'Not specified'}",
                f"Data quality score: {state.quality_scores.get(comp.name, 0.5):.2f}"
            ]
            
            profiles.append(ReportSection(
                title=f"Competitor Profile: {comp.name}",
                content=profile_content,
                key_insights=key_insights
            ))
        
        return profiles
    
    def _create_swot_analysis_section(self, state: AgentState) -> ReportSection:
        """Create SWOT analysis section"""
        swot = state.processed_data.get("swot_analysis", {})
        
        content = """
        SWOT Analysis
        
        This analysis examines internal strengths and weaknesses alongside external opportunities and threats.
        """
        
        # Strengths
        strengths = swot.get("strengths", [])
        if strengths:
            content += "\n\nSTRENGTHS:\n"
            for i, strength in enumerate(strengths, 1):
                content += f"{i}. {strength}\n"
        
        # Weaknesses
        weaknesses = swot.get("weaknesses", [])
        if weaknesses:
            content += "\nWEAKNESSES:\n"
            for i, weakness in enumerate(weaknesses, 1):
                content += f"{i}. {weakness}\n"
        
        # Opportunities
        opportunities = swot.get("opportunities", [])
        if opportunities:
            content += "\nOPPORTUNITIES:\n"
            for i, opportunity in enumerate(opportunities, 1):
                content += f"{i}. {opportunity}\n"
        
        # Threats
        threats = swot.get("threats", [])
        if threats:
            content += "\nTHREATS:\n"
            for i, threat in enumerate(threats, 1):
                content += f"{i}. {threat}\n"
        
        key_insights = [
            f"{len(strengths)} key strengths identified",
            f"{len(opportunities)} market opportunities available",
            f"{len(threats)} potential threats require attention"
        ]
        
        return ReportSection(
            title="SWOT Analysis",
            content=content,
            key_insights=key_insights
        )
    
    def _create_market_positioning_section(self, state: AgentState) -> ReportSection:
        """Create market positioning section"""
        positioning = state.processed_data.get("market_positioning", {})
        
        content = """
        Market Positioning Analysis
        
        This section analyzes the current market positioning and identifies opportunities for differentiation.
        """
        
        # Market gaps
        gaps = positioning.get("market_gaps", [])
        if gaps:
            content += "\n\nIdentified Market Gaps:\n"
            for gap in gaps:
                content += f"• {gap}\n"
        
        # Positioning opportunities
        opportunities = positioning.get("positioning_opportunities", [])
        if opportunities:
            content += "\nPositioning Opportunities:\n"
            for opp in opportunities:
                content += f"• {opp}\n"
        
        # Differentiation strategies
        strategies = positioning.get("differentiation_strategies", [])
        if strategies:
            content += "\nRecommended Differentiation Strategies:\n"
            for strategy in strategies:
                content += f"• {strategy}\n"
        
        key_insights = [
            "Multiple positioning opportunities identified",
            "Clear differentiation strategies available",
            "Market gaps present expansion opportunities"
        ]
        
        return ReportSection(
            title="Market Positioning",
            content=content,
            key_insights=key_insights
        )
    
    def _create_threats_opportunities_section(self, state: AgentState) -> ReportSection:
        """Create threats and opportunities section"""
        competitive_analysis = state.competitive_analysis
        
        content = """
        Threats and Opportunities Analysis
        
        This section provides detailed analysis of competitive threats and market opportunities.
        """
        
        # Opportunities
        if competitive_analysis and "opportunity_analysis" in competitive_analysis:
            opportunities = competitive_analysis["opportunity_analysis"]
            content += "\n\nKey Opportunities:\n"
            for i, opp in enumerate(opportunities[:5], 1):
                if isinstance(opp, dict):
                    content += f"{i}. {opp.get('opportunity', str(opp))}\n"
                    if "potential_impact" in opp:
                        content += f"   Impact: {opp['potential_impact']}\n"
                else:
                    content += f"{i}. {opp}\n"
        
        # Threats
        if competitive_analysis and "threat_analysis" in competitive_analysis:
            threats = competitive_analysis["threat_analysis"]
            content += "\nKey Threats:\n"
            for i, threat in enumerate(threats[:5], 1):
                if isinstance(threat, dict):
                    competitor = threat.get('competitor', 'Unknown')
                    threat_level = threat.get('threat_level', 'Medium')
                    content += f"{i}. {competitor} (Threat Level: {threat_level})\n"
                    
                    key_threats = threat.get('key_threats', [])
                    for kt in key_threats[:2]:
                        content += f"   • {kt}\n"
                else:
                    content += f"{i}. {threat}\n"
        
        key_insights = [
            "Multiple growth opportunities available",
            "Competitive threats require strategic response",
            "Market timing favorable for expansion"
        ]
        
        return ReportSection(
            title="Threats and Opportunities",
            content=content,
            key_insights=key_insights
        )
    
    def _create_strategic_recommendations_section(self, state: AgentState) -> ReportSection:
        """Create strategic recommendations section"""
        recommendations = state.recommendations
        
        content = """
        Strategic Recommendations
        
        Based on the comprehensive competitive analysis, the following strategic recommendations are proposed:
        """
        
        if recommendations:
            content += "\n\nPriority Recommendations:\n"
            for i, rec in enumerate(recommendations[:8], 1):
                content += f"{i}. {rec}\n"
        
        # Add implementation priorities
        content += "\n\nImplementation Priorities:\n"
        content += "• Short-term (0-6 months): Focus on immediate competitive responses\n"
        content += "• Medium-term (6-18 months): Develop differentiation strategies\n"
        content += "• Long-term (18+ months): Build sustainable competitive advantages\n"
        
        key_insights = [
            f"{len(recommendations)} strategic recommendations provided",
            "Clear implementation timeline established",
            "Focus on sustainable competitive advantage"
        ]
        
        return ReportSection(
            title="Strategic Recommendations",
            content=content,
            key_insights=key_insights
        )
    
    def _create_final_report(self, 
                           state: AgentState, 
                           executive_summary: str, 
                           sections: Dict[str, Any]) -> Report:
        """Create the final report object"""
        context = state.analysis_context
        
        # Extract main sections
        market_overview = sections.get("market_overview", ReportSection(title="Market Overview", content=""))
        competitive_landscape = sections.get("competitive_landscape", ReportSection(title="Competitive Landscape", content=""))
        swot_analysis = sections.get("swot_analysis", ReportSection(title="SWOT Analysis", content=""))
        market_positioning = sections.get("market_positioning", ReportSection(title="Market Positioning", content=""))
        threats_opportunities = sections.get("threats_opportunities", ReportSection(title="Threats and Opportunities", content=""))
        strategic_recommendations = sections.get("strategic_recommendations", ReportSection(title="Strategic Recommendations", content=""))
        
        # Get competitor profiles
        competitor_profiles = sections.get("competitor_profiles", [])
        
        report = Report(
            analysis_id=state.request_id,
            title=f"Competitive Analysis Report: {context.client_company}",
            executive_summary=executive_summary,
            client_company=context.client_company,
            industry=context.industry,
            market_overview=market_overview,
            competitive_landscape=competitive_landscape,
            competitor_profiles=competitor_profiles,
            swot_analysis=swot_analysis,
            market_positioning=market_positioning,
            threats_opportunities=threats_opportunities,
            strategic_recommendations=strategic_recommendations,
            total_competitors_analyzed=len(state.competitor_data),
            data_sources=context.data_sources,
            confidence_level="high" if len(state.get_high_quality_competitors()) > 5 else "medium"
        )
        
        return report