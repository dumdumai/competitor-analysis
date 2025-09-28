"""
LLM-powered Quality Agent that uses AI to assess data quality and generate structured feedback.
This agent leverages LLM capabilities to provide more intelligent quality assessment compared to rule-based approaches.
"""

import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
from pydantic import BaseModel, Field

from models.agent_state import AgentState, QualityIssue
from models.analysis import CompetitorData
from services.redis_service import RedisService
from services.llm_service import LLMService


class CompetitorQualityAssessment(BaseModel):
    """Structured output for competitor quality assessment"""
    competitor_name: str = Field(..., description="Name of the competitor being assessed")
    overall_quality_score: float = Field(..., description="Overall quality score from 0.0 to 1.0", ge=0.0, le=1.0)
    data_completeness_score: float = Field(..., description="Data completeness score from 0.0 to 1.0", ge=0.0, le=1.0)
    data_accuracy_score: float = Field(..., description="Data accuracy score from 0.0 to 1.0", ge=0.0, le=1.0)
    relevance_score: float = Field(..., description="Business relevance score from 0.0 to 1.0", ge=0.0, le=1.0)
    quality_issues: List[str] = Field(default_factory=list, description="List of specific quality issues identified")
    strengths: List[str] = Field(default_factory=list, description="List of data quality strengths")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Suggestions for data improvement")


class SimplifiedQualityIssue(BaseModel):
    """Simplified quality issue for LLM output"""
    issue_type: str = Field(..., description="Type: insufficient_competitors, analysis_depth, competitive_positioning, data_gaps")
    severity: str = Field(..., description="Severity: critical, high, medium, or low")
    description: str = Field(..., description="Detailed description of the issue")
    affected_competitors: List[str] = Field(default_factory=list, description="List of affected competitor names")
    suggested_action: str = Field(..., description="Specific action to resolve the issue")
    retry_agent: Optional[str] = Field(None, description="Agent to retry: search or analysis")


class LLMQualityAnalysisOutput(BaseModel):
    """Simplified output model for LLM quality analysis"""
    overall_assessment: str = Field(..., description="Overall quality assessment summary")
    total_competitors_analyzed: int = Field(..., description="Number of competitors analyzed")
    high_quality_competitors: int = Field(..., description="Number of high-quality competitors")
    average_quality_score: float = Field(..., description="Average quality score from 0.0 to 1.0", ge=0.0, le=1.0)
    critical_issues: List[SimplifiedQualityIssue] = Field(default_factory=list, description="List of critical quality issues")
    recommendations: List[str] = Field(default_factory=list, description="Overall recommendations for improvement")
    requires_human_review: bool = Field(..., description="Whether human review is required")
    analysis_confidence: float = Field(..., description="Confidence in the analysis from 0.0 to 1.0", ge=0.0, le=1.0)


class LLMQualityAgent:
    """
    Advanced quality assurance agent powered by LLM for intelligent data quality assessment.
    Provides structured output similar to the rule-based quality agent but with AI-driven insights.
    """

    def __init__(self, llm_service: LLMService, redis_service: RedisService):
        self.name = "llm_quality_agent"
        self.llm_service = llm_service
        self.redis_service = redis_service
        self.min_quality_threshold = 0.3

    async def process(self, state: AgentState) -> AgentState:
        """Execute LLM-powered quality assessment"""
        try:
            logger.info(f"🧠 Starting LLM-powered quality assessment for {len(state.discovered_competitors)} competitors")

            # Update progress
            await self._update_progress(state, "llm_quality", 5, "Initializing LLM quality assessment")

            # Process competitor data first (similar to original quality agent)
            await self._update_progress(state, "llm_quality", 20, "Processing competitor data")
            competitor_data_list = await self._process_competitor_data(state)

            # LLM-powered quality assessment
            await self._update_progress(state, "llm_quality", 50, "Analyzing data quality with AI")
            quality_assessments = await self._llm_assess_competitor_quality(competitor_data_list, state)

            # Generate overall quality analysis
            await self._update_progress(state, "llm_quality", 80, "Generating quality insights")
            overall_analysis = await self._llm_generate_quality_analysis(quality_assessments, state)

            # Update state with results
            await self._update_state_with_llm_results(state, competitor_data_list, quality_assessments, overall_analysis)

            # Final progress update
            high_quality_count = len([a for a in quality_assessments if a.overall_quality_score >= self.min_quality_threshold])
            await self._update_progress(state, "llm_quality", 100,
                                      f"LLM quality assessment completed: {high_quality_count}/{len(quality_assessments)} high-quality competitors")

            logger.info(f"✅ LLM quality assessment completed with {len(overall_analysis.critical_issues)} critical issues identified")
            return state

        except Exception as e:
            logger.error(f"❌ LLM Quality Agent failed: {e}")
            state.add_error(f"LLM quality assessment failed: {str(e)}")
            state.status = "failed"
            return state

    async def _process_competitor_data(self, state: AgentState) -> List[CompetitorData]:
        """Use existing rich competitor data from analysis agent if available, otherwise create basic data"""

        # First check if we already have rich competitor data from the analysis agent
        if hasattr(state, 'competitor_data') and state.competitor_data:
            logger.info(f"🔍 DEBUG: Using existing rich competitor data from analysis agent ({len(state.competitor_data)} competitors)")
            return state.competitor_data.copy()

        logger.info(f"🔍 DEBUG: No rich competitor data found, creating basic competitor data from search results")

        # Fallback: Convert discovered competitors to structured data (similar to original quality agent)
        competitor_data_list = []

        for competitor_name in state.discovered_competitors:
            # Get competitor details from search results
            competitor_details = next(
                (details for comp_name, details in state.search_results.items()
                 if comp_name.lower() == competitor_name.lower()),
                {}
            )

            # Create CompetitorData object with all required fields
            competitor_data = CompetitorData(
                name=competitor_name,
                description=competitor_details.get("description", "Competitor analysis data"),
                business_model=competitor_details.get("business_model", "Not specified"),
                target_market=competitor_details.get("target_market", state.analysis_context.target_market),
                website=competitor_details.get("website", ""),
                founding_year=competitor_details.get("founding_year"),
                employee_count=competitor_details.get("employees"),
                key_products=competitor_details.get("key_products", []),
                competitive_advantages=competitor_details.get("competitive_advantages", []),
                market_share=competitor_details.get("market_share"),
                recent_news=competitor_details.get("recent_news", [])
            )

            competitor_data_list.append(competitor_data)

        return competitor_data_list

    async def _llm_assess_competitor_quality(self, competitors: List[CompetitorData], state: AgentState) -> List[CompetitorQualityAssessment]:
        """Use LLM to assess the quality of each competitor's data"""
        assessments = []

        for competitor in competitors:
            try:
                # Prepare competitor data for LLM analysis
                competitor_summary = self._prepare_competitor_summary(competitor)

                # Create LLM prompt for quality assessment
                prompt = f"""
As an expert competitive intelligence analyst, evaluate this competitor data quality with specific, actionable insights.

COMPETITOR DATA:
{competitor_summary}

ANALYSIS CONTEXT:
- Client Company: {state.analysis_context.client_company}
- Industry: {state.analysis_context.industry}
- Target Market: {state.analysis_context.target_market}
- Business Model: {state.analysis_context.business_model}

QUALITY ASSESSMENT CRITERIA:
1. Data Completeness (0.0-1.0): Evaluate missing vs available information
2. Data Accuracy (0.0-1.0): Assess reliability and credibility of sources
3. Business Relevance (0.0-1.0): How directly competitive is this company to {state.analysis_context.client_company}

PROVIDE SPECIFIC INSIGHTS:
- Quality Issues: Be specific about what data is missing or questionable
- Strengths: Highlight what data points are particularly valuable
- Improvement Suggestions: Give actionable, specific recommendations (e.g., "Search for recent funding data from Crunchbase", "Look for customer reviews on G2 or Capterra", "Find technical documentation or API specs")

Overall Quality Score: 1.0=comprehensive competitive intelligence, 0.7+=good actionable data, 0.5-0.7=basic info sufficient, <0.5=insufficient for competitive analysis
"""

                # Get structured response from LLM
                assessment = await self.llm_service.get_structured_response(
                    prompt=prompt,
                    response_model=CompetitorQualityAssessment,
                    max_tokens=1000
                )

                # Ensure competitor name matches
                assessment.competitor_name = competitor.name
                assessments.append(assessment)

                logger.info(f"🔍 LLM assessed {competitor.name}: quality score {assessment.overall_quality_score:.2f}")

            except Exception as e:
                logger.error(f"❌ Failed to assess {competitor.name}: {e}")
                # Create fallback assessment
                fallback_assessment = CompetitorQualityAssessment(
                    competitor_name=competitor.name,
                    overall_quality_score=0.5,
                    data_completeness_score=0.5,
                    data_accuracy_score=0.5,
                    relevance_score=0.5,
                    quality_issues=[f"LLM assessment failed: {str(e)}"],
                    strengths=[],
                    improvement_suggestions=["Retry LLM assessment", "Manual data review needed"]
                )
                assessments.append(fallback_assessment)

        return assessments

    async def _llm_generate_quality_analysis(self, assessments: List[CompetitorQualityAssessment], state: AgentState) -> LLMQualityAnalysisOutput:
        """Use LLM to generate overall quality analysis and identify critical issues"""
        try:
            # Prepare summary of all assessments
            assessment_summary = self._prepare_assessment_summary(assessments)

            # Create LLM prompt for overall analysis
            prompt = f"""
As a senior competitive intelligence analyst, provide strategic quality assessment and specific actionable recommendations.

COMPETITOR QUALITY ASSESSMENTS:
{assessment_summary}

ANALYSIS CONTEXT:
- Client Company: {state.analysis_context.client_company}
- Industry: {state.analysis_context.industry}
- Target Market: {state.analysis_context.target_market}
- Business Model: {state.analysis_context.business_model}
- Expected Competitors: {state.analysis_context.max_competitors}
- Current Quality Threshold: {self.min_quality_threshold}

CRITICAL ISSUES FORMAT:
Each critical issue must be a JSON object with these exact field names:
{{
  "issue_type": "insufficient_competitors" | "analysis_depth" | "competitive_positioning" | "data_gaps",
  "severity": "critical" | "high" | "medium" | "low",
  "description": "Detailed description of the issue",
  "affected_competitors": ["CompanyA", "CompanyB"],
  "suggested_action": "Specific action to resolve the issue",
  "retry_agent": "search" | "analysis" | null
}}

EXAMPLE CRITICAL ISSUES:
- issue_type "insufficient_competitors": When fewer competitors found than expected
- issue_type "analysis_depth": When market analysis appears shallow or incomplete
- issue_type "competitive_positioning": When competitive analysis lacks depth
- issue_type "data_gaps": When key competitor information is missing

PROVIDE SPECIFIC, ACTIONABLE SUGGESTIONS:
- Search strategies: "Search for 'industry + startups + year', check AngelList, review industry reports"
- Data sources: "Pull market data from industry reports, check competitor websites for pricing, analyze LinkedIn for team sizes"
- Research methods: "Compare feature matrices, analyze case studies, review customer testimonials"

IMPORTANT: Use the exact field names shown above: "issue_type", "severity", "description", "affected_competitors", "suggested_action", "retry_agent".

STRATEGIC RECOMMENDATIONS:
Provide industry-specific, context-aware suggestions that would genuinely improve the competitive analysis quality for {state.analysis_context.client_company} in {state.analysis_context.industry}.
"""

            # Get structured response from LLM
            analysis = await self.llm_service.get_structured_response(
                prompt=prompt,
                response_model=LLMQualityAnalysisOutput,
                max_tokens=1500
            )

            # Update with actual counts
            analysis.total_competitors_analyzed = len(assessments)
            analysis.high_quality_competitors = len([a for a in assessments if a.overall_quality_score >= self.min_quality_threshold])
            analysis.average_quality_score = sum(a.overall_quality_score for a in assessments) / len(assessments) if assessments else 0.0

            return analysis

        except Exception as e:
            logger.error(f"❌ Failed to generate overall quality analysis: {e}")
            # Create fallback analysis
            high_quality_count = len([a for a in assessments if a.overall_quality_score >= self.min_quality_threshold])
            avg_quality = sum(a.overall_quality_score for a in assessments) / len(assessments) if assessments else 0.0

            return LLMQualityAnalysisOutput(
                overall_assessment=f"LLM analysis failed, fallback assessment: {high_quality_count}/{len(assessments)} competitors meet quality threshold",
                total_competitors_analyzed=len(assessments),
                high_quality_competitors=high_quality_count,
                average_quality_score=avg_quality,
                critical_issues=[
                    SimplifiedQualityIssue(
                        issue_type="llm_analysis_failure",
                        severity="high",
                        description=f"LLM quality analysis failed: {str(e)}",
                        affected_competitors=[a.competitor_name for a in assessments],
                        suggested_action="Retry LLM analysis or use manual quality assessment",
                        retry_agent="llm_quality"
                    )
                ],
                recommendations=["Retry LLM analysis", "Consider manual quality review"],
                requires_human_review=True,
                analysis_confidence=0.3
            )

    def _convert_to_quality_issues(self, simplified_issues: List[SimplifiedQualityIssue]) -> List[QualityIssue]:
        """Convert simplified LLM output to QualityIssue objects"""
        quality_issues = []
        for issue in simplified_issues:
            quality_issue = QualityIssue(
                issue_type=issue.issue_type,
                severity=issue.severity,
                description=issue.description,
                affected_competitors=issue.affected_competitors,
                suggested_action=issue.suggested_action,
                retry_agent=issue.retry_agent,
                additional_params={}
            )
            quality_issues.append(quality_issue)
        return quality_issues

    async def _update_state_with_llm_results(self, state: AgentState, competitors: List[CompetitorData],
                                           assessments: List[CompetitorQualityAssessment],
                                           analysis: LLMQualityAnalysisOutput):
        """Update agent state with LLM quality assessment results"""
        # Update competitor data
        state.competitor_data = competitors

        # Update quality scores
        state.quality_scores = {a.competitor_name: a.overall_quality_score for a in assessments}

        # Convert simplified quality issues to the expected format
        quality_issues = self._convert_to_quality_issues(analysis.critical_issues)

        # Add quality issues to retry context
        for issue in quality_issues:
            state.retry_context.quality_feedback.append(issue)

        # Store detailed assessments in state for later use
        state.llm_quality_assessments = {a.competitor_name: a for a in assessments}
        state.llm_quality_analysis = analysis

        logger.info(f"🔍 Updated state with {len(quality_issues)} critical issues from LLM analysis")

    def _prepare_competitor_summary(self, competitor: CompetitorData) -> str:
        """Prepare a summary of competitor data for LLM analysis"""
        summary_parts = [
            f"Name: {competitor.name}",
            f"Description: {competitor.description or 'Not available'}",
            f"Website: {competitor.website or 'Not available'}",
            f"Industry: {competitor.industry or 'Not available'}",
            f"Founded: {competitor.founded_year or 'Not available'}",
            f"Employees: {competitor.employees or 'Not available'}",
            f"Revenue: {competitor.revenue or 'Not available'}",
            f"Business Model: {competitor.business_model or 'Not available'}",
        ]

        if competitor.key_products:
            summary_parts.append(f"Key Products: {', '.join(competitor.key_products)}")

        if competitor.competitive_advantages:
            summary_parts.append(f"Competitive Advantages: {', '.join(competitor.competitive_advantages)}")

        if competitor.geographic_presence:
            summary_parts.append(f"Geographic Presence: {', '.join(competitor.geographic_presence)}")

        return "\\n".join(summary_parts)

    def _prepare_assessment_summary(self, assessments: List[CompetitorQualityAssessment]) -> str:
        """Prepare a summary of all quality assessments for LLM analysis"""
        summary_lines = []

        for assessment in assessments:
            lines = [
                f"\\nCompetitor: {assessment.competitor_name}",
                f"Overall Quality: {assessment.overall_quality_score:.2f}",
                f"Completeness: {assessment.data_completeness_score:.2f}",
                f"Accuracy: {assessment.data_accuracy_score:.2f}",
                f"Relevance: {assessment.relevance_score:.2f}",
            ]

            if assessment.quality_issues:
                lines.append(f"Issues: {', '.join(assessment.quality_issues)}")

            if assessment.strengths:
                lines.append(f"Strengths: {', '.join(assessment.strengths)}")

            summary_lines.extend(lines)

        return "\\n".join(summary_lines)

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
