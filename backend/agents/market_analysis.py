from typing import Dict, Any, List
from loguru import logger
from models.agent_state import AgentState
from services.llm_service import LLMService
from agents.data_collection import DataCollectionAgent


class MarketAnalysisAgent:
    """Agent responsible for analyzing market landscape and trends"""
    
    def __init__(self, llm_service: LLMService, data_collection_agent: DataCollectionAgent):
        self.name = "market_analysis"
        self.llm_service = llm_service
        self.data_collection_agent = data_collection_agent
    
    async def process(self, state: AgentState) -> AgentState:
        """Perform comprehensive market analysis"""
        try:
            logger.info(f"Starting market analysis for {state.analysis_context.industry} industry")
            
            # Update progress
            state.update_progress("market_analysis", 30)
            
            # Collect market data if not already available
            market_data = await self._ensure_market_data(state)
            state.update_progress("market_analysis", 50)
            
            # Analyze market landscape using LLM
            market_analysis = await self.llm_service.analyze_market_landscape(
                industry=state.analysis_context.industry,
                competitors=[comp.dict() for comp in state.competitor_data],
                search_results=market_data
            )
            
            state.update_progress("market_analysis", 70)
            
            # Enhance analysis with additional insights
            enhanced_analysis = await self._enhance_market_analysis(
                market_analysis, state
            )
            
            state.update_progress("market_analysis", 85)
            
            # Store results
            state.market_insights = enhanced_analysis
            state.processed_data["market_analysis"] = enhanced_analysis
            
            # Generate market positioning insights
            positioning_insights = self._generate_positioning_insights(state)
            state.processed_data["market_positioning"] = positioning_insights
            
            # Update metadata
            state.metadata.update({
                "market_analysis_completed": True,
                "market_segments_identified": len(enhanced_analysis.get("market_segments", [])),
                "key_trends_identified": len(enhanced_analysis.get("key_trends", [])),
                "competitive_intensity": enhanced_analysis.get("competitive_intensity", "unknown")
            })
            
            # Complete the stage
            state.complete_stage("market_analysis")
            state.update_progress("market_analysis", 100)
            
            logger.info("Market analysis completed successfully")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            state.add_error(f"Market analysis failed: {str(e)}")
            return state
    
    async def _ensure_market_data(self, state: AgentState) -> List[Dict[str, Any]]:
        """Ensure market data is available, collect if necessary"""
        # Check if market data already exists
        if "market_data" in state.search_results:
            return state.search_results["market_data"]
        
        # Collect fresh market data
        market_data = await self.data_collection_agent.collect_market_data(state)
        state.search_results["market_data"] = market_data
        
        return market_data
    
    async def _enhance_market_analysis(self, 
                                     base_analysis: Dict[str, Any], 
                                     state: AgentState) -> Dict[str, Any]:
        """Enhance market analysis with additional insights"""
        try:
            enhanced = base_analysis.copy()
            
            # Add competitor-based insights
            competitor_insights = self._analyze_competitor_patterns(state.competitor_data)
            enhanced["competitor_insights"] = competitor_insights
            
            # Add market maturity analysis
            maturity_analysis = self._analyze_market_maturity(state)
            enhanced["market_maturity"] = maturity_analysis
            
            # Add entry barriers analysis
            barriers_analysis = self._analyze_entry_barriers(state, base_analysis)
            enhanced["detailed_barriers"] = barriers_analysis
            
            # Add opportunity scoring
            opportunities = self._score_opportunities(base_analysis, state)
            enhanced["scored_opportunities"] = opportunities
            
            # Add threat assessment
            threats = self._assess_market_threats(base_analysis, state)
            enhanced["threat_assessment"] = threats
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing market analysis: {e}")
            return base_analysis
    
    def _analyze_competitor_patterns(self, competitors: List) -> Dict[str, Any]:
        """Analyze patterns across competitors"""
        if not competitors:
            return {}
        
        insights = {
            "total_competitors": len(competitors),
            "business_model_distribution": {},
            "geographic_distribution": {},
            "size_distribution": {},
            "common_strengths": [],
            "common_weaknesses": [],
            "technology_trends": []
        }
        
        # Analyze business models
        business_models = {}
        for comp in competitors:
            bm = getattr(comp, 'business_model', 'Unknown')
            business_models[bm] = business_models.get(bm, 0) + 1
        insights["business_model_distribution"] = business_models
        
        # Analyze geographic presence
        headquarters = {}
        for comp in competitors:
            hq = getattr(comp, 'headquarters', 'Unknown')
            if hq and hq != 'Unknown':
                # Extract country/region
                location = hq.split(',')[-1].strip() if ',' in hq else hq
                headquarters[location] = headquarters.get(location, 0) + 1
        insights["geographic_distribution"] = headquarters
        
        # Analyze company sizes
        sizes = {"Large": 0, "Medium": 0, "Small": 0, "Unknown": 0}
        for comp in competitors:
            employee_count = getattr(comp, 'employee_count', '')
            if isinstance(employee_count, str):
                if any(term in employee_count.lower() for term in ['1000+', '10000+', 'large']):
                    sizes["Large"] += 1
                elif any(term in employee_count.lower() for term in ['100-', '500-', 'medium']):
                    sizes["Medium"] += 1
                elif any(term in employee_count.lower() for term in ['1-', '50-', 'small']):
                    sizes["Small"] += 1
                else:
                    sizes["Unknown"] += 1
            else:
                sizes["Unknown"] += 1
        insights["size_distribution"] = sizes
        
        # Analyze common strengths and weaknesses
        all_strengths = []
        all_weaknesses = []
        all_tech = []
        
        for comp in competitors:
            strengths = getattr(comp, 'strengths', [])
            weaknesses = getattr(comp, 'weaknesses', [])
            tech_stack = getattr(comp, 'technology_stack', [])
            
            if isinstance(strengths, list):
                all_strengths.extend(strengths)
            if isinstance(weaknesses, list):
                all_weaknesses.extend(weaknesses)
            if isinstance(tech_stack, list):
                all_tech.extend(tech_stack)
        
        # Find most common strengths/weaknesses
        from collections import Counter
        
        strength_counts = Counter(all_strengths)
        insights["common_strengths"] = [
            {"strength": s, "count": c} 
            for s, c in strength_counts.most_common(5)
        ]
        
        weakness_counts = Counter(all_weaknesses)
        insights["common_weaknesses"] = [
            {"weakness": w, "count": c} 
            for w, c in weakness_counts.most_common(5)
        ]
        
        tech_counts = Counter(all_tech)
        insights["technology_trends"] = [
            {"technology": t, "count": c} 
            for t, c in tech_counts.most_common(5)
        ]
        
        return insights
    
    def _analyze_market_maturity(self, state: AgentState) -> Dict[str, Any]:
        """Analyze market maturity based on competitor data"""
        competitors = state.competitor_data
        
        maturity_indicators = {
            "founding_years": [],
            "funding_stages": [],
            "market_consolidation": "unknown",
            "innovation_level": "unknown",
            "maturity_score": 0.0
        }
        
        if not competitors:
            return maturity_indicators
        
        # Analyze founding years
        founding_years = []
        for comp in competitors:
            year = getattr(comp, 'founding_year', None)
            if year and isinstance(year, int) and 1900 <= year <= 2024:
                founding_years.append(year)
        
        maturity_indicators["founding_years"] = founding_years
        
        if founding_years:
            avg_age = 2024 - sum(founding_years) / len(founding_years)
            recent_companies = len([y for y in founding_years if y >= 2015])
            
            # Determine maturity level
            if avg_age > 20 and recent_companies < len(founding_years) * 0.3:
                maturity_level = "Mature"
                maturity_score = 0.8
            elif avg_age > 10 and recent_companies < len(founding_years) * 0.5:
                maturity_level = "Growing"
                maturity_score = 0.6
            else:
                maturity_level = "Emerging"
                maturity_score = 0.3
            
            maturity_indicators["maturity_level"] = maturity_level
            maturity_indicators["maturity_score"] = maturity_score
            maturity_indicators["average_company_age"] = round(avg_age, 1)
            maturity_indicators["recent_entrants_percentage"] = round(recent_companies / len(founding_years) * 100, 1)
        
        return maturity_indicators
    
    def _analyze_entry_barriers(self, 
                              state: AgentState, 
                              base_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market entry barriers in detail"""
        barriers = base_analysis.get("barriers_to_entry", [])
        competitors = state.competitor_data
        
        detailed_barriers = {
            "capital_requirements": {"level": "unknown", "evidence": []},
            "regulatory_barriers": {"level": "unknown", "evidence": []},
            "technology_barriers": {"level": "unknown", "evidence": []},
            "network_effects": {"level": "unknown", "evidence": []},
            "brand_loyalty": {"level": "unknown", "evidence": []},
            "overall_barrier_level": "medium"
        }
        
        # Analyze based on competitor characteristics
        if competitors:
            # Technology barriers
            tech_complexity = 0
            for comp in competitors:
                tech_stack = getattr(comp, 'technology_stack', [])
                if isinstance(tech_stack, list) and len(tech_stack) > 5:
                    tech_complexity += 1
            
            if tech_complexity > len(competitors) * 0.6:
                detailed_barriers["technology_barriers"]["level"] = "high"
                detailed_barriers["technology_barriers"]["evidence"] = [
                    "Many competitors use complex technology stacks"
                ]
            
            # Brand loyalty (based on company age and market position)
            established_companies = 0
            for comp in competitors:
                year = getattr(comp, 'founding_year', None)
                if year and isinstance(year, int) and year < 2010:
                    established_companies += 1
            
            if established_companies > len(competitors) * 0.5:
                detailed_barriers["brand_loyalty"]["level"] = "high"
                detailed_barriers["brand_loyalty"]["evidence"] = [
                    "Many established competitors with long market presence"
                ]
        
        return detailed_barriers
    
    def _score_opportunities(self, 
                           base_analysis: Dict[str, Any], 
                           state: AgentState) -> List[Dict[str, Any]]:
        """Score market opportunities"""
        opportunities = base_analysis.get("emerging_opportunities", [])
        scored_opportunities = []
        
        for i, opportunity in enumerate(opportunities):
            # Simple scoring based on various factors
            score = {
                "opportunity": opportunity,
                "attractiveness_score": 0.7,  # Default medium attractiveness
                "feasibility_score": 0.6,    # Default medium feasibility
                "urgency_score": 0.5,        # Default medium urgency
                "overall_score": 0.6
            }
            
            # Adjust scores based on keywords (simplified logic)
            opp_lower = opportunity.lower() if isinstance(opportunity, str) else ""
            
            # High attractiveness indicators
            if any(word in opp_lower for word in ["ai", "automation", "digital", "cloud"]):
                score["attractiveness_score"] = 0.8
            
            # High urgency indicators
            if any(word in opp_lower for word in ["emerging", "growing", "trend"]):
                score["urgency_score"] = 0.7
            
            # Calculate overall score
            score["overall_score"] = (
                score["attractiveness_score"] * 0.4 + 
                score["feasibility_score"] * 0.3 + 
                score["urgency_score"] * 0.3
            )
            
            scored_opportunities.append(score)
        
        # Sort by overall score
        scored_opportunities.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return scored_opportunities
    
    def _assess_market_threats(self, 
                             base_analysis: Dict[str, Any], 
                             state: AgentState) -> Dict[str, Any]:
        """Assess market threats in detail"""
        threats = base_analysis.get("market_threats", [])
        
        threat_assessment = {
            "immediate_threats": [],
            "medium_term_threats": [],
            "long_term_threats": [],
            "threat_severity": "medium",
            "mitigation_priority": []
        }
        
        for threat in threats:
            threat_info = {
                "threat": threat,
                "timeline": "medium-term",
                "severity": "medium",
                "probability": "medium"
            }
            
            # Categorize threats by timeline and severity (simplified)
            threat_lower = threat.lower() if isinstance(threat, str) else ""
            
            if any(word in threat_lower for word in ["disruption", "regulation", "economic"]):
                threat_info["severity"] = "high"
                threat_info["timeline"] = "immediate"
                threat_assessment["immediate_threats"].append(threat_info)
            elif any(word in threat_lower for word in ["competition", "market"]):
                threat_info["timeline"] = "medium-term"
                threat_assessment["medium_term_threats"].append(threat_info)
            else:
                threat_info["timeline"] = "long-term"
                threat_assessment["long_term_threats"].append(threat_info)
        
        return threat_assessment
    
    def _generate_positioning_insights(self, state: AgentState) -> Dict[str, Any]:
        """Generate market positioning insights"""
        competitors = state.competitor_data
        context = state.analysis_context
        
        positioning = {
            "market_gaps": [],
            "positioning_opportunities": [],
            "differentiation_strategies": [],
            "competitive_positioning_map": {}
        }
        
        if not competitors:
            return positioning
        
        # Identify potential market gaps
        business_models = set()
        target_markets = set()
        
        for comp in competitors:
            bm = getattr(comp, 'business_model', '')
            tm = getattr(comp, 'target_market', '')
            
            if bm:
                business_models.add(bm.lower())
            if tm:
                target_markets.add(tm.lower())
        
        # Suggest potential gaps (simplified logic)
        all_business_models = {
            "saas", "marketplace", "b2b", "b2c", "freemium", 
            "subscription", "enterprise", "consulting"
        }
        
        potential_gaps = all_business_models - business_models
        positioning["market_gaps"] = [
            f"Limited presence in {gap} business model" 
            for gap in list(potential_gaps)[:3]
        ]
        
        # Generate positioning opportunities
        positioning["positioning_opportunities"] = [
            "Focus on underserved market segments",
            "Differentiate through superior customer experience",
            "Leverage technology for competitive advantage",
            "Target specific industry verticals"
        ]
        
        return positioning