import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger
from models.agent_state import AgentState
from services.llm_service import LLMService
from services.redis_service import RedisService


class ReportAgent:
    """
    Unified report generation and delivery agent.
    Handles final report compilation, formatting, and delivery.
    """
    
    def __init__(self, llm_service: LLMService, redis_service: RedisService, report_repository=None):
        self.name = "report_agent"
        self.llm_service = llm_service
        self.redis_service = redis_service
        self.report_repository = report_repository
    
    async def process(self, state: AgentState) -> AgentState:
        """Execute comprehensive report generation and delivery"""
        try:
            logger.info(f"📊 Starting report generation for {state.analysis_context.client_company}")
            
            # Update progress
            await self._update_progress(state, "report", 5, "Initializing report generation")
            
            # Stage 1: Compile report data
            await self._update_progress(state, "report", 20, "Compiling analysis results")
            report_data = await self._compile_report_data(state)
            
            # Stage 2: Generate executive summary
            await self._update_progress(state, "report", 40, "Generating executive summary")
            executive_summary = await self._generate_executive_summary(state, report_data)
            
            # Stage 3: Create detailed sections
            await self._update_progress(state, "report", 60, "Creating detailed report sections")
            detailed_sections = await self._create_detailed_sections(state, report_data)
            
            # Stage 4: Compile final report
            await self._update_progress(state, "report", 80, "Assembling final report")
            final_report = await self._compile_final_report(state, executive_summary, detailed_sections, report_data)
            
            # Stage 5: Store and deliver report
            await self._update_progress(state, "report", 95, "Storing and delivering report")
            await self._store_and_deliver_report(state, final_report)
            
            # Update state with final results
            state.processed_data["final_report"] = final_report
            state.processed_data["executive_summary"] = executive_summary
            
            # Update metadata
            state.metadata.update({
                "report_generated": True,
                "report_sections": len(detailed_sections),
                "total_competitors_in_report": len(state.competitor_data),
                "report_generation_completed": True,
                "final_status": "completed"
            })
            
            # Mark as completed
            state.status = "completed"
            state.complete_stage("report")
            await self._update_progress(state, "report", 100, f"Report completed: {len(state.competitor_data)} competitors analyzed")
            
            logger.info(f"✅ Report generation completed successfully for {state.analysis_context.client_company}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in report agent: {e}")
            state.add_error(f"Report generation failed: {str(e)}")
            state.status = "failed"
            return state
    
    async def _compile_report_data(self, state: AgentState) -> Dict[str, Any]:
        """Compile all analysis data for report generation"""
        return {
            "analysis_context": {
                "client_company": state.analysis_context.client_company,
                "industry": state.analysis_context.industry,
                "target_market": state.analysis_context.target_market,
                "business_model": state.analysis_context.business_model,
                "analysis_date": datetime.utcnow().isoformat()
            },
            "competitors": [competitor.dict() for competitor in state.competitor_data],
            "market_insights": state.market_insights,
            "competitive_analysis": state.competitive_analysis,
            "recommendations": state.recommendations,
            "quality_metrics": {
                "total_competitors": len(state.discovered_competitors),
                "analyzed_competitors": len(state.competitor_data),
                "average_quality_score": state.metadata.get("average_quality_score", 0),
                "high_quality_competitors": state.metadata.get("high_quality_competitors", 0)
            },
            "search_statistics": {
                "total_searches": sum(len(results) for results in state.search_results.values()),
                "data_sources": list(state.search_results.keys()),
                "search_completed_stages": state.completed_stages
            }
        }
    
    async def _generate_executive_summary(self, state: AgentState, report_data: Dict[str, Any]) -> str:
        """Generate executive summary using AI"""
        try:
            if not self.llm_service.client:
                return self._generate_fallback_executive_summary(state, report_data)
            
            context = state.analysis_context
            competitors = report_data["competitors"]
            market_insights = report_data["market_insights"]
            competitive_analysis = report_data["competitive_analysis"]
            
            summary_prompt = f"""
            Generate a comprehensive executive summary for a competitive analysis report.
            
            Client: {context.client_company}
            Industry: {context.industry}
            Target Market: {context.target_market}
            Business Model: {context.business_model}
            
            Analysis Results:
            - {len(competitors)} competitors analyzed
            - Market insights: {json.dumps(market_insights, indent=2)[:500]}...
            - Competitive analysis: {json.dumps(competitive_analysis, indent=2)[:500]}...
            
            Create a 300-400 word executive summary that covers:
            1. Market landscape overview
            2. Key competitive findings
            3. Strategic implications
            4. Priority recommendations
            
            Write in a professional, strategic tone suitable for executives.
            """
            
            response = await self.llm_service.client.chat.completions.create(
                model=self.llm_service.model,
                messages=[
                    {"role": "system", "content": "You are a senior business consultant writing an executive summary."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI executive summary: {e}")
            return self._generate_fallback_executive_summary(state, report_data)
    
    def _generate_fallback_executive_summary(self, state: AgentState, report_data: Dict[str, Any]) -> str:
        """Generate basic executive summary without AI"""
        context = state.analysis_context
        competitors_count = len(report_data["competitors"])
        
        return f"""
EXECUTIVE SUMMARY

This competitive analysis provides a comprehensive overview of the competitive landscape for {context.client_company} in the {context.industry} industry within the {context.target_market} market.

KEY FINDINGS:
• Analyzed {competitors_count} key competitors in the market
• Identified market opportunities and competitive threats
• Assessed competitive positioning and strategic gaps
• Generated actionable recommendations for market success

MARKET LANDSCAPE:
The {context.industry} market shows dynamic competitive activity with established players and emerging challengers. Our analysis reveals significant opportunities for differentiation and market positioning.

COMPETITIVE POSITIONING:
{context.client_company} operates in a competitive environment where success depends on clear differentiation, strong execution, and strategic market positioning.

STRATEGIC RECOMMENDATIONS:
Based on our analysis, we recommend focusing on competitive advantages, addressing market gaps, and leveraging unique positioning opportunities to achieve sustainable growth.

This analysis provides the foundation for strategic decision-making and competitive positioning in the {context.target_market} market.
        """.strip()
    
    async def _create_detailed_sections(self, state: AgentState, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed report sections"""
        sections = {}
        
        # Section 1: Market Overview
        sections["market_overview"] = self._create_market_overview_section(report_data)
        
        # Section 2: Competitive Landscape
        sections["competitive_landscape"] = self._create_competitive_landscape_section(report_data)
        
        # Section 3: Competitor Profiles
        sections["competitor_profiles"] = self._create_competitor_profiles_section(report_data)
        
        # Section 4: Strategic Analysis
        sections["strategic_analysis"] = self._create_strategic_analysis_section(report_data)
        
        # Section 5: Recommendations
        sections["recommendations"] = self._create_recommendations_section(report_data)
        
        # Section 6: Data Quality & Methodology
        sections["methodology"] = self._create_methodology_section(report_data)
        
        return sections
    
    def _create_market_overview_section(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create market overview section"""
        market_insights = report_data.get("market_insights", {})
        
        return {
            "title": "Market Overview",
            "content": {
                "market_size": market_insights.get("market_size", "Market size analysis not available"),
                "key_trends": market_insights.get("key_trends", ["Market trends analysis pending"]),
                "competitive_intensity": market_insights.get("competitive_intensity", "Medium"),
                "opportunities": market_insights.get("opportunities", ["Market opportunities to be identified"]),
                "threats": market_insights.get("threats", ["Market threats to be assessed"]),
                "outlook": market_insights.get("outlook", "Market outlook pending analysis")
            },
            "summary": f"The market shows {market_insights.get('competitive_intensity', 'moderate')} competitive intensity with several key trends shaping the landscape."
        }
    
    def _create_competitive_landscape_section(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create competitive landscape section"""
        competitive_analysis = report_data.get("competitive_analysis", {})
        competitors = report_data.get("competitors", [])
        
        # Categorize competitors by market position
        market_leaders = [c for c in competitors if c.get("market_position", "").lower() in ["market leader", "leader", "dominant"]]
        challengers = [c for c in competitors if "challenger" in c.get("market_position", "").lower()]
        emerging_players = [c for c in competitors if "emerging" in c.get("market_position", "").lower()]
        
        return {
            "title": "Competitive Landscape",
            "content": {
                "total_competitors": len(competitors),
                "market_leaders": [c["name"] for c in market_leaders],
                "challengers": [c["name"] for c in challengers],
                "emerging_players": [c["name"] for c in emerging_players],
                "positioning": competitive_analysis.get("positioning", "Competitive positioning analysis pending"),
                "key_differentiators": competitive_analysis.get("competitive_advantages", []),
                "market_gaps": competitive_analysis.get("competitive_gaps", [])
            },
            "summary": f"Analysis of {len(competitors)} competitors reveals {len(market_leaders)} market leaders, {len(challengers)} challengers, and {len(emerging_players)} emerging players."
        }
    
    def _create_competitor_profiles_section(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed competitor profiles section"""
        competitors = report_data.get("competitors", [])
        
        profiles = []
        for competitor in competitors[:10]:  # Limit to top 10 for report clarity
            profile = {
                "name": competitor.get("name", "Unknown"),
                "website": competitor.get("website", ""),
                "description": competitor.get("description", "No description available"),
                "business_model": competitor.get("business_model", "Unknown"),
                "key_products": competitor.get("key_products", []),
                "strengths": competitor.get("strengths", []),
                "weaknesses": competitor.get("weaknesses", []),
                "market_position": competitor.get("market_position", "Unknown"),
                "competitive_advantages": competitor.get("competitive_advantages", [])
            }
            profiles.append(profile)
        
        return {
            "title": "Competitor Profiles",
            "content": {
                "profiles": profiles,
                "total_analyzed": len(competitors),
                "profiles_included": len(profiles)
            },
            "summary": f"Detailed profiles of {len(profiles)} key competitors, including business models, strengths, and market positioning."
        }
    
    def _create_strategic_analysis_section(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create strategic analysis section"""
        competitive_analysis = report_data.get("competitive_analysis", {})
        market_insights = report_data.get("market_insights", {})
        
        return {
            "title": "Strategic Analysis",
            "content": {
                "competitive_threats": competitive_analysis.get("threat_assessment", "Medium"),
                "market_opportunities": market_insights.get("opportunities", []),
                "differentiation_opportunities": competitive_analysis.get("differentiation_opportunities", []),
                "barriers_to_entry": market_insights.get("barriers_to_entry", []),
                "success_factors": market_insights.get("key_success_factors", []),
                "technology_trends": market_insights.get("technology_disruptions", [])
            },
            "summary": "Strategic analysis reveals key opportunities for differentiation and competitive positioning."
        }
    
    def _create_recommendations_section(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create recommendations section"""
        recommendations = report_data.get("recommendations", [])
        
        # Categorize recommendations
        strategic_recs = [r for r in recommendations if any(keyword in r.lower() for keyword in ["strategy", "position", "market"])]
        product_recs = [r for r in recommendations if any(keyword in r.lower() for keyword in ["product", "feature", "development"])]
        marketing_recs = [r for r in recommendations if any(keyword in r.lower() for keyword in ["marketing", "brand", "customer"])]
        operational_recs = [r for r in recommendations if r not in strategic_recs + product_recs + marketing_recs]
        
        return {
            "title": "Strategic Recommendations",
            "content": {
                "strategic": strategic_recs,
                "product": product_recs,
                "marketing": marketing_recs,
                "operational": operational_recs,
                "all_recommendations": recommendations,
                "total_recommendations": len(recommendations)
            },
            "summary": f"Generated {len(recommendations)} actionable recommendations across strategic, product, marketing, and operational areas."
        }
    
    def _create_methodology_section(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create methodology and data quality section"""
        quality_metrics = report_data.get("quality_metrics", {})
        search_stats = report_data.get("search_statistics", {})
        
        return {
            "title": "Methodology & Data Quality",
            "content": {
                "data_sources": search_stats.get("data_sources", []),
                "total_searches": search_stats.get("total_searches", 0),
                "competitors_discovered": quality_metrics.get("total_competitors", 0),
                "competitors_analyzed": quality_metrics.get("analyzed_competitors", 0),
                "average_quality_score": quality_metrics.get("average_quality_score", 0),
                "high_quality_competitors": quality_metrics.get("high_quality_competitors", 0),
                "analysis_stages": search_stats.get("search_completed_stages", []),
                "quality_threshold": "60% minimum data completeness and accuracy"
            },
            "summary": f"Analysis based on {search_stats.get('total_searches', 0)} searches across multiple data sources with {quality_metrics.get('average_quality_score', 0)*100:.0f}% average data quality."
        }
    
    async def _compile_final_report(self, state: AgentState, executive_summary: str, sections: Dict[str, Any], report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile the final comprehensive report"""
        context = state.analysis_context
        
        final_report = {
            "metadata": {
                "report_title": f"Competitive Analysis Report: {context.client_company}",
                "client_company": context.client_company,
                "industry": context.industry,
                "target_market": context.target_market,
                "business_model": context.business_model,
                "generation_date": datetime.utcnow().isoformat(),
                "report_version": "1.0",
                "analysis_id": state.request_id
            },
            "executive_summary": executive_summary,
            "sections": sections,
            "raw_data": report_data,
            "appendices": {
                "competitor_data": [competitor.dict() for competitor in state.competitor_data],
                "search_results_summary": {
                    "total_data_points": sum(len(results) for results in state.search_results.values()),
                    "data_categories": list(state.search_results.keys())
                },
                "quality_scores": state.quality_scores,
                "analysis_timeline": {
                    "started_at": state.started_at.isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "completed_stages": state.completed_stages
                }
            }
        }
        
        return final_report
    
    async def _store_and_deliver_report(self, state: AgentState, final_report: Dict[str, Any]):
        """Store the final report and prepare for delivery"""
        try:
            # Store full report in Redis
            await self.redis_service.store_analysis_result(state.request_id, final_report)
            
            # Save report to MongoDB if repository is available
            if self.report_repository:
                try:
                    from models.report import Report
                    from datetime import datetime
                    
                    # Create Report model from final_report data
                    competitor_profiles_section = final_report["sections"].get("competitor_profiles", {})
                    competitor_profiles = competitor_profiles_section.get("profiles", []) if isinstance(competitor_profiles_section, dict) else []
                    
                    report = Report(
                        analysis_id=state.request_id,
                        title=final_report["metadata"]["report_title"],
                        executive_summary=final_report["executive_summary"],
                        client_company=final_report["metadata"]["client_company"],
                        industry=final_report["metadata"]["industry"],
                        analysis_date=datetime.utcnow(),
                        market_overview=final_report["sections"]["market_overview"],
                        competitive_landscape=final_report["sections"]["competitive_landscape"],
                        competitor_profiles=competitor_profiles,
                        swot_analysis=final_report["sections"].get("swot_analysis", {}),
                        market_positioning=final_report["sections"].get("market_positioning", {}),
                        threats_opportunities=final_report["sections"].get("threats_opportunities", {}),
                        strategic_recommendations=final_report["sections"]["recommendations"],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    # Save to database
                    report_id = await self.report_repository.create_report(report)
                    logger.info(f"📊 Report saved to database with ID: {report_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to save report to database: {e}")
                    # Continue anyway - report is still in Redis
            
            # Store condensed version for quick access
            condensed_report = {
                "metadata": final_report["metadata"],
                "executive_summary": final_report["executive_summary"],
                "key_findings": {
                    "competitors_analyzed": len(state.competitor_data),
                    "recommendations_count": len(state.recommendations),
                    "quality_score": state.metadata.get("average_quality_score", 0)
                },
                "status": "completed"
            }
            
            await self.redis_service.store_progress_update(state.request_id, {
                "stage": "completed",
                "progress": 100,
                "message": "Analysis completed successfully",
                "timestamp": asyncio.get_event_loop().time(),
                "report_ready": True,
                "condensed_report": condensed_report
            })
            
            logger.info(f"📊 Report stored and ready for delivery: {state.request_id}")
            
        except Exception as e:
            logger.error(f"Error storing report: {e}")
            raise
    
    async def _update_progress(self, state: AgentState, stage: str, progress: int, message: str):
        """Update progress with detailed status"""
        state.progress = progress
        state.current_stage = stage
        
        # Store progress update for real-time display
        progress_update = {
            "stage": stage,
            "progress": progress,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Store in Redis for real-time updates
        await self.redis_service.store_progress_update(state.request_id, progress_update)
        
        logger.info(f"📊 Progress {progress}%: {message}")