from typing import Dict, Any, List
from loguru import logger
from models.agent_state import AgentState
from services.llm_service import LLMService


class CompetitiveAnalysisAgent:
    """Agent responsible for performing competitive analysis and generating strategic insights"""
    
    def __init__(self, llm_service: LLMService):
        self.name = "competitive_analysis"
        self.llm_service = llm_service
    
    async def process(self, state: AgentState) -> AgentState:
        """Perform comprehensive competitive analysis"""
        try:
            logger.info(f"Starting competitive analysis for {state.analysis_context.client_company}")
            
            # Update progress
            state.update_progress("competitive_analysis", 35)
            
            # Get high-quality competitors for analysis
            high_quality_competitors = state.get_high_quality_competitors(0.6)
            
            if not high_quality_competitors:
                state.add_warning("No high-quality competitors found for competitive analysis")
                # Still try with all available competitors
                high_quality_competitors = state.competitor_data[:10]  # Limit to top 10
            
            state.update_progress("competitive_analysis", 50)
            
            # Perform LLM-based competitive analysis
            competitive_analysis = await self.llm_service.generate_competitive_analysis(
                client_company=state.analysis_context.client_company,
                competitors=[comp.dict() for comp in high_quality_competitors],
                market_analysis=state.market_insights
            )
            
            state.update_progress("competitive_analysis", 70)
            
            # Enhance analysis with detailed competitor comparisons
            enhanced_analysis = await self._enhance_competitive_analysis(
                competitive_analysis, state
            )
            
            state.update_progress("competitive_analysis", 85)
            
            # Generate SWOT analysis
            swot_analysis = self._generate_swot_analysis(enhanced_analysis, state)
            
            # Store results
            state.competitive_analysis = enhanced_analysis
            state.processed_data["competitive_analysis"] = enhanced_analysis
            state.processed_data["swot_analysis"] = swot_analysis
            
            # Generate strategic recommendations
            recommendations = self._extract_strategic_recommendations(enhanced_analysis)
            state.recommendations = recommendations
            
            # Update metadata
            state.metadata.update({
                "competitive_analysis_completed": True,
                "competitors_analyzed": len(high_quality_competitors),
                "threats_identified": len(enhanced_analysis.get("threat_analysis", [])),
                "opportunities_identified": len(enhanced_analysis.get("opportunity_analysis", [])),
                "recommendations_generated": len(recommendations)
            })
            
            # Complete the stage
            state.complete_stage("competitive_analysis")
            state.update_progress("competitive_analysis", 100)
            
            logger.info("Competitive analysis completed successfully")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in competitive analysis: {e}")
            state.add_error(f"Competitive analysis failed: {str(e)}")
            return state
    
    async def _enhance_competitive_analysis(self, 
                                          base_analysis: Dict[str, Any], 
                                          state: AgentState) -> Dict[str, Any]:
        """Enhance competitive analysis with additional insights"""
        enhanced = base_analysis.copy()
        
        # Add detailed competitor comparison matrix
        comparison_matrix = self._create_competitor_comparison_matrix(state)
        enhanced["competitor_comparison_matrix"] = comparison_matrix
        
        # Add competitive intensity analysis
        intensity_analysis = self._analyze_competitive_intensity(state)
        enhanced["competitive_intensity_analysis"] = intensity_analysis
        
        # Add market share analysis
        market_share_analysis = self._analyze_market_share_distribution(state)
        enhanced["market_share_analysis"] = market_share_analysis
        
        # Add competitive dynamics
        dynamics = self._analyze_competitive_dynamics(state)
        enhanced["competitive_dynamics"] = dynamics
        
        return enhanced
    
    def _create_competitor_comparison_matrix(self, state: AgentState) -> Dict[str, Any]:
        """Create a detailed competitor comparison matrix"""
        competitors = state.competitor_data
        
        if not competitors:
            return {}
        
        comparison_factors = [
            "market_position", "product_quality", "pricing_strategy", 
            "technology_sophistication", "customer_base", "geographic_reach",
            "financial_strength", "brand_recognition"
        ]
        
        matrix = {
            "factors": comparison_factors,
            "competitors": [],
            "client_positioning": {}
        }
        
        for comp in competitors:
            competitor_scores = {
                "name": comp.name,
                "overall_score": 0.0,
                "factor_scores": {}
            }
            
            # Score each factor (simplified scoring logic)
            total_score = 0
            scored_factors = 0
            
            for factor in comparison_factors:
                score = self._score_competitor_factor(comp, factor)
                competitor_scores["factor_scores"][factor] = score
                if score > 0:
                    total_score += score
                    scored_factors += 1
            
            if scored_factors > 0:
                competitor_scores["overall_score"] = total_score / scored_factors
            
            matrix["competitors"].append(competitor_scores)
        
        # Sort competitors by overall score
        matrix["competitors"].sort(key=lambda x: x["overall_score"], reverse=True)
        
        return matrix
    
    def _score_competitor_factor(self, competitor, factor: str) -> float:
        """Score a competitor on a specific factor (0-1 scale)"""
        # This is a simplified scoring system
        # In a real implementation, this would be more sophisticated
        
        if factor == "market_position":
            position = getattr(competitor, 'market_position', '')
            if isinstance(position, str):
                if any(word in position.lower() for word in ['leader', 'dominant', 'top']):
                    return 0.9
                elif any(word in position.lower() for word in ['strong', 'established']):
                    return 0.7
                elif any(word in position.lower() for word in ['growing', 'emerging']):
                    return 0.5
            return 0.4
        
        elif factor == "pricing_strategy":
            pricing = getattr(competitor, 'pricing_strategy', '')
            if isinstance(pricing, str) and len(pricing) > 10:
                return 0.7
            return 0.3
        
        elif factor == "technology_sophistication":
            tech_stack = getattr(competitor, 'technology_stack', [])
            if isinstance(tech_stack, list):
                if len(tech_stack) > 5:
                    return 0.8
                elif len(tech_stack) > 2:
                    return 0.6
                elif len(tech_stack) > 0:
                    return 0.4
            return 0.2
        
        elif factor == "financial_strength":
            funding = getattr(competitor, 'funding_info', {})
            if isinstance(funding, dict) and funding:
                return 0.7
            return 0.4
        
        elif factor == "product_quality":
            strengths = getattr(competitor, 'strengths', [])
            if isinstance(strengths, list):
                quality_indicators = ['quality', 'reliable', 'performance', 'features']
                if any(any(indicator in str(strength).lower() for indicator in quality_indicators) 
                      for strength in strengths):
                    return 0.8
                elif len(strengths) > 2:
                    return 0.6
            return 0.5
        
        # Default scoring for other factors
        return 0.5
    
    def _analyze_competitive_intensity(self, state: AgentState) -> Dict[str, Any]:
        """Analyze the competitive intensity of the market"""
        competitors = state.competitor_data
        
        intensity = {
            "overall_intensity": "medium",
            "intensity_score": 0.5,
            "key_factors": [],
            "intensity_drivers": []
        }
        
        if not competitors:
            return intensity
        
        # Calculate intensity based on various factors
        intensity_factors = {
            "number_of_competitors": len(competitors),
            "market_maturity": state.processed_data.get("market_analysis", {}).get("market_maturity", {}),
            "differentiation_level": 0,
            "switching_costs": "unknown"
        }
        
        # Analyze differentiation level
        business_models = set()
        for comp in competitors:
            bm = getattr(comp, 'business_model', '')
            if bm:
                business_models.add(bm.lower())
        
        differentiation_score = len(business_models) / max(len(competitors), 1)
        intensity_factors["differentiation_level"] = differentiation_score
        
        # Calculate overall intensity score
        score = 0.5  # Base score
        
        # Adjust based on number of competitors
        if len(competitors) > 15:
            score += 0.2
        elif len(competitors) > 10:
            score += 0.1
        elif len(competitors) < 5:
            score -= 0.1
        
        # Adjust based on differentiation
        if differentiation_score < 0.3:
            score += 0.2  # Low differentiation = high intensity
        elif differentiation_score > 0.7:
            score -= 0.1  # High differentiation = lower intensity
        
        intensity["intensity_score"] = min(max(score, 0.0), 1.0)
        
        # Determine intensity level
        if intensity["intensity_score"] > 0.7:
            intensity["overall_intensity"] = "high"
        elif intensity["intensity_score"] > 0.4:
            intensity["overall_intensity"] = "medium"
        else:
            intensity["overall_intensity"] = "low"
        
        intensity["key_factors"] = intensity_factors
        
        return intensity
    
    def _analyze_market_share_distribution(self, state: AgentState) -> Dict[str, Any]:
        """Analyze market share distribution among competitors"""
        competitors = state.competitor_data
        
        distribution = {
            "market_concentration": "unknown",
            "top_players": [],
            "market_fragmentation": "medium",
            "concentration_ratio": 0.0
        }
        
        # Get competitors with market share data
        competitors_with_share = []
        for comp in competitors:
            market_share = getattr(comp, 'market_share', None)
            if market_share and isinstance(market_share, (int, float)) and market_share > 0:
                competitors_with_share.append({
                    "name": comp.name,
                    "market_share": market_share
                })
        
        if competitors_with_share:
            # Sort by market share
            competitors_with_share.sort(key=lambda x: x["market_share"], reverse=True)
            
            # Calculate concentration ratio (top 4 players)
            top_4_share = sum(comp["market_share"] for comp in competitors_with_share[:4])
            distribution["concentration_ratio"] = top_4_share
            distribution["top_players"] = competitors_with_share[:5]
            
            # Determine market concentration
            if top_4_share > 60:
                distribution["market_concentration"] = "highly_concentrated"
            elif top_4_share > 40:
                distribution["market_concentration"] = "moderately_concentrated"
            else:
                distribution["market_concentration"] = "fragmented"
        
        return distribution
    
    def _analyze_competitive_dynamics(self, state: AgentState) -> Dict[str, Any]:
        """Analyze competitive dynamics and relationships"""
        competitors = state.competitor_data
        
        dynamics = {
            "competitive_groups": [],
            "rivalry_patterns": [],
            "collaboration_opportunities": [],
            "disruption_potential": "medium"
        }
        
        if not competitors:
            return dynamics
        
        # Group competitors by similar characteristics
        groups = self._identify_competitive_groups(competitors)
        dynamics["competitive_groups"] = groups
        
        # Identify rivalry patterns
        rivalry = self._identify_rivalry_patterns(competitors)
        dynamics["rivalry_patterns"] = rivalry
        
        return dynamics
    
    def _identify_competitive_groups(self, competitors) -> List[Dict[str, Any]]:
        """Identify strategic groups of competitors"""
        # Simple grouping by business model and size
        groups = {}
        
        for comp in competitors:
            business_model = getattr(comp, 'business_model', 'Unknown')
            employee_count = getattr(comp, 'employee_count', '')
            
            # Determine size category
            size = "Unknown"
            if isinstance(employee_count, str):
                if any(term in employee_count.lower() for term in ['1000+', 'large']):
                    size = "Large"
                elif any(term in employee_count.lower() for term in ['100-', 'medium']):
                    size = "Medium"
                elif any(term in employee_count.lower() for term in ['small', '1-']):
                    size = "Small"
            
            group_key = f"{business_model}_{size}"
            
            if group_key not in groups:
                groups[group_key] = {
                    "group_name": f"{business_model} - {size}",
                    "business_model": business_model,
                    "size_category": size,
                    "members": []
                }
            
            groups[group_key]["members"].append({
                "name": comp.name,
                "key_strengths": getattr(comp, 'strengths', [])[:2]
            })
        
        return list(groups.values())
    
    def _identify_rivalry_patterns(self, competitors) -> List[str]:
        """Identify patterns of rivalry between competitors"""
        patterns = []
        
        # Analyze based on similar target markets
        target_markets = {}
        for comp in competitors:
            target_market = getattr(comp, 'target_market', '')
            if target_market:
                if target_market not in target_markets:
                    target_markets[target_market] = []
                target_markets[target_market].append(comp.name)
        
        # Identify markets with high competition
        for market, comps in target_markets.items():
            if len(comps) > 3:
                patterns.append(f"Intense rivalry in {market} market among: {', '.join(comps[:3])}")
        
        return patterns
    
    def _generate_swot_analysis(self, 
                              competitive_analysis: Dict[str, Any], 
                              state: AgentState) -> Dict[str, Any]:
        """Generate SWOT analysis based on competitive analysis"""
        swot = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        }
        
        # Extract from competitive analysis
        opportunities = competitive_analysis.get("opportunity_analysis", [])
        threats = competitive_analysis.get("threat_analysis", [])
        
        # Convert opportunities
        for opp in opportunities:
            if isinstance(opp, dict):
                swot["opportunities"].append(opp.get("opportunity", str(opp)))
            else:
                swot["opportunities"].append(str(opp))
        
        # Convert threats
        for threat in threats:
            if isinstance(threat, dict):
                swot["threats"].append(threat.get("competitor", str(threat)))
            else:
                swot["threats"].append(str(threat))
        
        # Add market-based opportunities and threats
        market_insights = state.market_insights
        if market_insights:
            market_opportunities = market_insights.get("emerging_opportunities", [])
            market_threats = market_insights.get("market_threats", [])
            
            swot["opportunities"].extend(market_opportunities[:3])
            swot["threats"].extend(market_threats[:3])
        
        # Generate generic strengths and weaknesses (would be more sophisticated in real implementation)
        swot["strengths"] = [
            "Deep industry knowledge and expertise",
            "Established client relationships",
            "Agile and responsive to market changes"
        ]
        
        swot["weaknesses"] = [
            "Limited brand recognition compared to major players",
            "Smaller marketing budget than competitors",
            "Dependence on key personnel"
        ]
        
        return swot
    
    def _extract_strategic_recommendations(self, 
                                         competitive_analysis: Dict[str, Any]) -> List[str]:
        """Extract strategic recommendations from competitive analysis"""
        recommendations = []
        
        # Extract from competitive analysis recommendations
        strategic_recs = competitive_analysis.get("strategic_recommendations", [])
        
        for rec in strategic_recs:
            if isinstance(rec, dict):
                recommendation = rec.get("recommendation", "")
                if recommendation:
                    recommendations.append(recommendation)
            elif isinstance(rec, str):
                recommendations.append(rec)
        
        # Add default recommendations if none found
        if not recommendations:
            recommendations = [
                "Focus on differentiating value proposition",
                "Strengthen competitive advantages",
                "Monitor competitor moves closely",
                "Invest in customer retention",
                "Explore strategic partnerships"
            ]
        
        return recommendations[:10]  # Limit to top 10 recommendations