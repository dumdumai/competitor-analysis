from typing import Dict, Any, List, Tuple
from loguru import logger
from models.agent_state import AgentState
from models.analysis import CompetitorData


class QualityAssuranceAgent:
    """Agent responsible for ensuring data quality and completeness"""
    
    def __init__(self):
        self.name = "quality_assurance"
        self.min_quality_score = 0.6
        self.critical_fields = ["name", "description", "business_model"]
        self.preferred_fields = [
            "website", "target_market", "key_products", 
            "strengths", "weaknesses", "market_position"
        ]
    
    async def process(self, state: AgentState) -> AgentState:
        """Perform quality assurance on processed competitor data"""
        try:
            logger.info(f"Starting quality assurance for {len(state.competitor_data)} competitors")
            
            # Update progress
            state.update_progress("quality_assurance", 25)
            
            if not state.competitor_data:
                state.add_warning("No competitor data found for quality assurance")
                state.complete_stage("quality_assurance")
                return state
            
            # Evaluate data quality for each competitor
            quality_results = []
            
            for i, competitor in enumerate(state.competitor_data):
                # Update progress
                progress = 25 + int((i / len(state.competitor_data)) * 60)
                state.update_progress("quality_assurance", progress)
                
                quality_score = self._evaluate_competitor_quality(competitor)
                quality_results.append({
                    "competitor_name": competitor.name,
                    "quality_score": quality_score,
                    "meets_threshold": quality_score >= self.min_quality_score
                })
                
                # Store quality score in state
                state.set_quality_score(competitor.name, quality_score)
            
            # Generate quality report
            quality_report = self._generate_quality_report(quality_results, state)
            state.processed_data["quality_report"] = quality_report
            
            # Filter high-quality competitors
            high_quality_competitors = state.get_high_quality_competitors(self.min_quality_score)
            
            # Update metadata
            state.metadata.update({
                "total_competitors_evaluated": len(quality_results),
                "high_quality_competitors": len(high_quality_competitors),
                "average_quality_score": sum(r["quality_score"] for r in quality_results) / len(quality_results),
                "quality_threshold_met": len([r for r in quality_results if r["meets_threshold"]]),
                "quality_assurance_completed": True
            })
            
            # Log quality insights
            self._log_quality_insights(quality_results, state)
            
            # Complete the stage
            state.complete_stage("quality_assurance")
            state.update_progress("quality_assurance", 100)
            
            logger.info(f"Quality assurance completed. {len(high_quality_competitors)} competitors meet quality threshold")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in quality assurance: {e}")
            state.add_error(f"Quality assurance failed: {str(e)}")
            return state
    
    def _evaluate_competitor_quality(self, competitor: CompetitorData) -> float:
        """Evaluate the quality of a single competitor's data"""
        total_score = 0.0
        max_score = 0.0
        
        # Critical fields evaluation (40% of total score)
        critical_score = 0.0
        critical_max = len(self.critical_fields)
        
        for field in self.critical_fields:
            field_value = getattr(competitor, field, None)
            if self._is_field_complete(field_value):
                critical_score += 1
        
        total_score += (critical_score / critical_max) * 0.4
        max_score += 0.4
        
        # Preferred fields evaluation (30% of total score)
        preferred_score = 0.0
        preferred_max = len(self.preferred_fields)
        
        for field in self.preferred_fields:
            field_value = getattr(competitor, field, None)
            if self._is_field_complete(field_value):
                preferred_score += 1
        
        total_score += (preferred_score / preferred_max) * 0.3
        max_score += 0.3
        
        # List fields completeness (20% of total score)
        list_fields = ["key_products", "strengths", "weaknesses", "competitive_advantages"]
        list_score = 0.0
        list_max = len(list_fields)
        
        for field in list_fields:
            field_value = getattr(competitor, field, [])
            if isinstance(field_value, list) and len(field_value) > 0:
                list_score += 1
        
        total_score += (list_score / list_max) * 0.2
        max_score += 0.2
        
        # Content quality evaluation (10% of total score)
        content_score = self._evaluate_content_quality(competitor)
        total_score += content_score * 0.1
        max_score += 0.1
        
        # Return normalized score (0-1)
        return total_score / max_score if max_score > 0 else 0.0
    
    def _is_field_complete(self, field_value) -> bool:
        """Check if a field has complete and meaningful data"""
        if field_value is None:
            return False
        
        if isinstance(field_value, str):
            # Check for meaningful content
            if len(field_value.strip()) < 3:
                return False
            
            # Check for common placeholder or error text
            placeholder_indicators = [
                "unknown", "n/a", "not available", "no information", 
                "error", "failed", "insufficient data"
            ]
            
            field_lower = field_value.lower()
            if any(indicator in field_lower for indicator in placeholder_indicators):
                return False
            
            return True
        
        if isinstance(field_value, list):
            return len(field_value) > 0
        
        if isinstance(field_value, dict):
            return len(field_value) > 0 and any(v for v in field_value.values())
        
        return True
    
    def _evaluate_content_quality(self, competitor: CompetitorData) -> float:
        """Evaluate the quality of textual content"""
        quality_score = 0.0
        evaluations = 0
        
        # Evaluate description quality
        description = competitor.description
        if description and isinstance(description, str):
            desc_quality = self._evaluate_text_quality(description)
            quality_score += desc_quality
            evaluations += 1
        
        # Evaluate business model description
        business_model = competitor.business_model
        if business_model and isinstance(business_model, str):
            bm_quality = self._evaluate_text_quality(business_model)
            quality_score += bm_quality
            evaluations += 1
        
        # Evaluate market position description
        market_position = competitor.market_position
        if market_position and isinstance(market_position, str):
            mp_quality = self._evaluate_text_quality(market_position)
            quality_score += mp_quality
            evaluations += 1
        
        return quality_score / evaluations if evaluations > 0 else 0.0
    
    def _evaluate_text_quality(self, text: str) -> float:
        """Evaluate the quality of a text field"""
        if not text or len(text.strip()) < 10:
            return 0.0
        
        # Basic quality indicators
        quality_score = 0.0
        
        # Length indicator (longer descriptions are generally better)
        if len(text) > 50:
            quality_score += 0.3
        elif len(text) > 20:
            quality_score += 0.2
        else:
            quality_score += 0.1
        
        # Word count indicator
        word_count = len(text.split())
        if word_count > 10:
            quality_score += 0.3
        elif word_count > 5:
            quality_score += 0.2
        else:
            quality_score += 0.1
        
        # Completeness indicator (no obvious truncation)
        if not text.endswith("...") and not "truncated" in text.lower():
            quality_score += 0.2
        
        # Avoid generic descriptions
        generic_indicators = ["company", "business", "service", "product"]
        unique_words = len([word for word in text.lower().split() 
                          if word not in generic_indicators])
        
        if unique_words > word_count * 0.7:  # More than 70% unique words
            quality_score += 0.2
        
        return min(quality_score, 1.0)  # Cap at 1.0
    
    def _generate_quality_report(self, 
                               quality_results: List[Dict[str, Any]], 
                               state: AgentState) -> Dict[str, Any]:
        """Generate a comprehensive quality report"""
        total_competitors = len(quality_results)
        high_quality_count = len([r for r in quality_results if r["meets_threshold"]])
        average_score = sum(r["quality_score"] for r in quality_results) / total_competitors
        
        # Categorize competitors by quality
        excellent = len([r for r in quality_results if r["quality_score"] >= 0.8])
        good = len([r for r in quality_results if 0.6 <= r["quality_score"] < 0.8])
        fair = len([r for r in quality_results if 0.4 <= r["quality_score"] < 0.6])
        poor = len([r for r in quality_results if r["quality_score"] < 0.4])
        
        # Identify data gaps
        data_gaps = self._identify_data_gaps(state.competitor_data)
        
        report = {
            "summary": {
                "total_competitors": total_competitors,
                "high_quality_competitors": high_quality_count,
                "average_quality_score": round(average_score, 3),
                "quality_threshold": self.min_quality_score
            },
            "quality_distribution": {
                "excellent (0.8+)": excellent,
                "good (0.6-0.8)": good,
                "fair (0.4-0.6)": fair,
                "poor (<0.4)": poor
            },
            "competitor_scores": [
                {
                    "name": r["competitor_name"],
                    "score": round(r["quality_score"], 3),
                    "meets_threshold": r["meets_threshold"]
                }
                for r in sorted(quality_results, key=lambda x: x["quality_score"], reverse=True)
            ],
            "data_gaps": data_gaps,
            "recommendations": self._generate_quality_recommendations(quality_results, data_gaps)
        }
        
        return report
    
    def _identify_data_gaps(self, competitors: List[CompetitorData]) -> Dict[str, Any]:
        """Identify common data gaps across competitors"""
        field_completeness = {}
        total_competitors = len(competitors)
        
        # Check all fields
        all_fields = self.critical_fields + self.preferred_fields + [
            "website", "founding_year", "headquarters", "employee_count",
            "funding_info", "pricing_strategy", "technology_stack", "partnerships"
        ]
        
        for field in all_fields:
            complete_count = 0
            for competitor in competitors:
                field_value = getattr(competitor, field, None)
                if self._is_field_complete(field_value):
                    complete_count += 1
            
            field_completeness[field] = {
                "complete": complete_count,
                "missing": total_competitors - complete_count,
                "completeness_rate": complete_count / total_competitors if total_competitors > 0 else 0
            }
        
        # Identify most common gaps
        gaps = {
            field: data for field, data in field_completeness.items()
            if data["completeness_rate"] < 0.5
        }
        
        return {
            "field_completeness": field_completeness,
            "major_gaps": gaps,
            "gap_summary": f"{len(gaps)} fields have less than 50% completeness"
        }
    
    def _generate_quality_recommendations(self, 
                                        quality_results: List[Dict[str, Any]], 
                                        data_gaps: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving data quality"""
        recommendations = []
        
        # Overall quality recommendations
        low_quality_count = len([r for r in quality_results if not r["meets_threshold"]])
        if low_quality_count > 0:
            recommendations.append(
                f"Consider additional data collection for {low_quality_count} competitors "
                f"that fall below the quality threshold"
            )
        
        # Data gap recommendations
        major_gaps = data_gaps.get("major_gaps", {})
        if len(major_gaps) > 3:
            recommendations.append(
                "Focus on collecting data for commonly missing fields: " + 
                ", ".join(list(major_gaps.keys())[:3])
            )
        
        # Source diversification
        recommendations.append(
            "Consider using additional data sources to improve completeness"
        )
        
        # Quality threshold adjustment
        avg_score = sum(r["quality_score"] for r in quality_results) / len(quality_results)
        if avg_score < self.min_quality_score:
            recommendations.append(
                f"Average quality score ({avg_score:.2f}) is below threshold. "
                f"Consider adjusting expectations or improving data collection"
            )
        
        return recommendations
    
    def _log_quality_insights(self, quality_results: List[Dict[str, Any]], state: AgentState):
        """Log key quality insights"""
        high_quality = [r for r in quality_results if r["meets_threshold"]]
        low_quality = [r for r in quality_results if not r["meets_threshold"]]
        
        logger.info(f"Quality Assessment Summary:")
        logger.info(f"  - High Quality Competitors: {len(high_quality)}")
        logger.info(f"  - Low Quality Competitors: {len(low_quality)}")
        
        if low_quality:
            low_quality_names = [r["competitor_name"] for r in low_quality[:3]]
            logger.warning(f"  - Competitors needing improvement: {', '.join(low_quality_names)}")
        
        if high_quality:
            avg_high_quality = sum(r["quality_score"] for r in high_quality) / len(high_quality)
            logger.info(f"  - Average high-quality score: {avg_high_quality:.2f}")