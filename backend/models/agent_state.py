from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .analysis import AnalysisRequest, CompetitorData


class QualityIssue(BaseModel):
    """Quality issue detected by QualityAgent"""
    issue_type: str = Field(..., description="Type of quality issue (data_completeness, accuracy, relevance, etc.)")
    severity: str = Field(..., description="Severity level: critical, high, medium, low")
    description: str = Field(..., description="Detailed description of the issue")
    affected_competitors: List[str] = Field(default_factory=list, description="Competitors affected by this issue")
    suggested_action: str = Field(..., description="Suggested action to resolve the issue")
    retry_agent: Optional[str] = Field(None, description="Which agent should retry (search, analysis)")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for retry")


class HumanReviewDecision(BaseModel):
    """Human decision on quality issues"""
    decision: str = Field(..., description="proceed, retry_search, retry_analysis, modify_params, or abort")
    feedback: Optional[str] = Field(None, description="Human feedback on the quality issues")
    modified_params: Dict[str, Any] = Field(default_factory=dict, description="Modified parameters if decision is modify_params")
    selected_issues: List[str] = Field(default_factory=list, description="Specific quality issues to address")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentRetryContext(BaseModel):
    """Context for agent retries based on quality feedback"""
    retry_count: int = Field(default=0, description="Number of retries attempted")
    max_retries: int = Field(default=2, description="Maximum number of retries allowed")
    quality_feedback: List[QualityIssue] = Field(default_factory=list, description="Quality issues to address")
    last_retry_agent: Optional[str] = Field(None, description="Last agent that was retried")
    retry_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of retry attempts")
    awaiting_human_review: bool = Field(default=False, description="Whether the workflow is waiting for human review")
    human_decision: Optional[HumanReviewDecision] = Field(None, description="Human decision on quality issues")


class SearchLog(BaseModel):
    """Log entry for a single search operation"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    search_type: str = Field(..., description="Type of search (competitor_search, company_details, market_analysis, etc.)")
    query: str = Field(..., description="The actual search query sent to Tavily")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Search parameters (max_results, search_depth, etc.)")
    results_count: int = Field(default=0, description="Number of results returned")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Raw results from Tavily")
    processing_notes: Optional[str] = Field(None, description="Notes about how results were processed")
    duration_ms: Optional[int] = Field(None, description="Time taken for search in milliseconds")
    error: Optional[str] = Field(None, description="Error message if search failed")


class AnalysisContext(BaseModel):
    client_company: str
    industry: str
    target_market: str
    business_model: str
    specific_requirements: Optional[str] = None
    max_competitors: int = 10
    
    # Product comparison fields
    comparison_type: str = Field(default="company", description="Type: 'company' or 'product'")
    client_product: Optional[str] = None
    product_category: Optional[str] = None
    comparison_criteria: List[str] = Field(default_factory=list)
    
    search_keywords: List[str] = Field(default_factory=list)
    excluded_domains: List[str] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    quality_requirements: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    analysis_context: AnalysisContext = Field(..., description="Analysis context and parameters")
    current_stage: str = Field(default="client_onboarding", description="Current analysis stage")
    completed_stages: List[str] = Field(default_factory=list, description="Completed stages")
    discovered_competitors: List[str] = Field(default_factory=list, description="List of discovered competitor names")
    competitor_data: List[CompetitorData] = Field(default_factory=list, description="Collected competitor data")
    
    # Product comparison fields
    discovered_products: List[str] = Field(default_factory=list, description="List of discovered product names")
    product_data: List[Dict[str, Any]] = Field(default_factory=list, description="Collected product data")
    product_comparisons: List[Dict[str, Any]] = Field(default_factory=list, description="Product comparison results")
    
    search_results: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="Raw search results by query")
    search_logs: List[SearchLog] = Field(default_factory=list, description="Detailed logs of all searches performed")
    processed_data: Dict[str, Any] = Field(default_factory=dict, description="Processed and structured data")
    quality_scores: Dict[str, float] = Field(default_factory=dict, description="Quality scores for each competitor")
    llm_quality_assessments: Dict[str, Any] = Field(default_factory=dict, description="LLM quality assessments for each competitor")
    llm_quality_analysis: Optional[Any] = Field(None, description="Overall LLM quality analysis result")
    market_insights: Dict[str, Any] = Field(default_factory=dict, description="Market analysis insights")
    competitive_analysis: Dict[str, Any] = Field(default_factory=dict, description="Competitive analysis results")
    recommendations: List[str] = Field(default_factory=list, description="Generated recommendations")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Any warnings encountered")
    progress: int = Field(default=0, description="Overall progress percentage")
    status: str = Field(default="in_progress", description="Current status")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    retry_context: AgentRetryContext = Field(default_factory=AgentRetryContext, description="Context for agent retries")
    search_guidance: Dict[str, Any] = Field(default_factory=dict, description="Guidance for search agent retries")
    analysis_guidance: Dict[str, Any] = Field(default_factory=dict, description="Guidance for analysis agent retries")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_progress(self, stage: str, progress: int):
        """Update the current stage and progress"""
        self.current_stage = stage
        self.progress = progress
        self.updated_at = datetime.utcnow()
        
        if stage not in self.completed_stages:
            # Don't mark as completed until 100%
            pass
    
    def complete_stage(self, stage: str):
        """Mark a stage as completed"""
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        self.updated_at = datetime.utcnow()
    
    def add_competitor(self, competitor_name: str):
        """Add a discovered competitor"""
        if competitor_name not in self.discovered_competitors:
            self.discovered_competitors.append(competitor_name)
        self.updated_at = datetime.utcnow()
    
    def add_competitor_data(self, competitor_data: CompetitorData):
        """Add processed competitor data"""
        # Replace if already exists, otherwise append
        existing_names = [c.name for c in self.competitor_data]
        if competitor_data.name in existing_names:
            for i, c in enumerate(self.competitor_data):
                if c.name == competitor_data.name:
                    self.competitor_data[i] = competitor_data
                    break
        else:
            self.competitor_data.append(competitor_data)
        self.updated_at = datetime.utcnow()
    
    def add_error(self, error_message: str):
        """Add an error message"""
        self.errors.append(f"{datetime.utcnow().isoformat()}: {error_message}")
        self.updated_at = datetime.utcnow()
    
    def add_warning(self, warning_message: str):
        """Add a warning message"""
        self.warnings.append(f"{datetime.utcnow().isoformat()}: {warning_message}")
        self.updated_at = datetime.utcnow()
    
    def set_quality_score(self, competitor_name: str, score: float):
        """Set quality score for a competitor"""
        self.quality_scores[competitor_name] = score
        self.updated_at = datetime.utcnow()
    
    def get_high_quality_competitors(self, min_score: float = 0.7) -> List[CompetitorData]:
        """Get competitors with quality score above threshold"""
        high_quality = []
        for competitor in self.competitor_data:
            if self.quality_scores.get(competitor.name, 0) >= min_score:
                high_quality.append(competitor)
        return high_quality
    
    def add_search_log(self, search_log: SearchLog):
        """Add a search log entry"""
        self.search_logs.append(search_log)
        self.updated_at = datetime.utcnow()
    
    def add_quality_issue(self, issue: 'QualityIssue'):
        """Add a quality issue for potential retry"""
        self.retry_context.quality_feedback.append(issue)
        self.updated_at = datetime.utcnow()
    
    def get_critical_quality_issues(self) -> List['QualityIssue']:
        """Get critical and high severity quality issues that require retries"""
        return [issue for issue in self.retry_context.quality_feedback 
                if issue.severity in ['critical', 'high']]
    
    def get_all_quality_issues_for_review(self) -> List['QualityIssue']:
        """Get all quality issues that may need human review (critical, high, and significant medium issues)"""
        return [issue for issue in self.retry_context.quality_feedback 
                if issue.severity in ['critical', 'high'] or 
                (issue.severity == 'medium' and issue.issue_type in ['overall_quality_low', 'recommendations_quality', 'analysis_depth'])]
    
    def can_retry(self) -> bool:
        """Check if more retries are allowed"""
        return self.retry_context.retry_count < self.retry_context.max_retries
    
    def should_retry(self) -> bool:
        """Check if should retry based on quality issues"""
        return self.can_retry() and bool(self.get_critical_quality_issues())
    
    def get_next_retry_agent(self) -> Optional[str]:
        """Get the next agent that should retry based on quality issues"""
        critical_issues = self.get_critical_quality_issues()
        if not critical_issues:
            return None
        
        # Prioritize search issues first, then analysis
        for issue in critical_issues:
            if issue.retry_agent == 'search':
                return 'search'
        
        for issue in critical_issues:
            if issue.retry_agent == 'analysis':
                return 'analysis'
        
        return None
    
    def record_retry(self, agent_name: str, reason: str):
        """Record a retry attempt"""
        self.retry_context.retry_count += 1
        self.retry_context.last_retry_agent = agent_name
        self.retry_context.retry_history.append({
            "agent": agent_name,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_number": self.retry_context.retry_count
        })
        self.updated_at = datetime.utcnow()
    
    def clear_quality_feedback(self):
        """Clear quality feedback after processing"""
        self.retry_context.quality_feedback.clear()
        self.updated_at = datetime.utcnow()
    
    def set_awaiting_human_review(self, awaiting: bool = True):
        """Set the workflow to await human review"""
        self.retry_context.awaiting_human_review = awaiting
        self.updated_at = datetime.utcnow()
    
    def set_human_decision(self, decision: 'HumanReviewDecision'):
        """Set the human decision for quality issues"""
        self.retry_context.human_decision = decision
        self.retry_context.awaiting_human_review = False
        self.updated_at = datetime.utcnow()
    
    def get_human_decision(self) -> Optional['HumanReviewDecision']:
        """Get the current human decision"""
        return self.retry_context.human_decision
    
    def is_awaiting_human_review(self) -> bool:
        """Check if workflow is waiting for human review"""
        return self.retry_context.awaiting_human_review
    
    def has_critical_issues_needing_review(self) -> bool:
        """Check if there are critical issues that need human review"""
        # Check for critical/high issues OR significant medium issues
        review_worthy_issues = self.get_all_quality_issues_for_review()
        return len(review_worthy_issues) > 0
    
    def apply_human_decision(self):
        """Apply the human decision to modify state"""
        decision = self.retry_context.human_decision
        if not decision:
            return
        
        if decision.decision == "modify_params":
            # Apply parameter modifications
            for key, value in decision.modified_params.items():
                if hasattr(self.analysis_context, key):
                    setattr(self.analysis_context, key, value)
        
        # Clear processed quality feedback if human decided to proceed or retry
        if decision.decision in ["proceed", "retry_search", "retry_analysis"]:
            if decision.selected_issues:
                # Only clear selected issues
                self.retry_context.quality_feedback = [
                    issue for issue in self.retry_context.quality_feedback
                    if issue.issue_type not in decision.selected_issues
                ]
            else:
                # Clear all quality feedback
                self.clear_quality_feedback()
        
        self.updated_at = datetime.utcnow()