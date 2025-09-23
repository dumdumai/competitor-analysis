from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class QualityIssue(BaseModel):
    issue_type: str = Field(..., description="Type of quality issue")
    severity: str = Field(..., description="Severity level: critical, high, medium, low")
    description: str = Field(..., description="Description of the issue")
    affected_competitors: List[str] = Field(default_factory=list, description="List of affected competitors")
    suggested_action: str = Field(..., description="Suggested action to resolve")
    retry_agent: Optional[str] = Field(None, description="Agent to retry if applicable")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")


class HumanReviewDecision(BaseModel):
    decision: str = Field(..., description="Human decision: proceed, retry_search, retry_analysis, modify_params, abort")
    feedback: Optional[str] = Field(None, description="Human feedback")
    modified_params: Optional[Dict[str, Any]] = Field(None, description="Modified parameters")
    selected_issues: Optional[List[str]] = Field(None, description="Selected issues to address")
    reviewed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of review")
    reviewer: Optional[str] = Field(None, description="Reviewer identifier")


class QualityReview(BaseModel):
    quality_issues: List[QualityIssue] = Field(default_factory=list, description="List of quality issues found")
    quality_scores: Dict[str, float] = Field(default_factory=dict, description="Quality scores per competitor")
    average_quality_score: float = Field(default=0.0, description="Average quality score")
    review_required: bool = Field(default=False, description="Whether human review is required")
    review_decision: Optional[HumanReviewDecision] = Field(None, description="Human review decision")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When quality review was created")
    completed_at: Optional[datetime] = Field(None, description="When quality review was completed")


class AnalysisRequest(BaseModel):
    client_company: str = Field(..., description="Name of the client company")
    industry: str = Field(..., description="Industry sector")
    target_market: str = Field(..., description="Target market or geographic region")
    business_model: str = Field(..., description="Business model description")
    specific_requirements: Optional[str] = Field(None, description="Specific analysis requirements")
    max_competitors: int = Field(default=10, description="Maximum number of competitors to analyze")
    
    # Product comparison fields
    comparison_type: str = Field(default="company", description="Type of comparison: 'company' or 'product'")
    client_product: Optional[str] = Field(None, description="Client product name for product-specific comparison")
    product_category: Optional[str] = Field(None, description="Product category for comparison")
    comparison_criteria: List[str] = Field(
        default_factory=list,
        description="Specific criteria for comparison (features, pricing, performance, etc.)"
    )
    demo_mode: bool = Field(default=False, description="Whether to use demo mode for searches")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CompetitorData(BaseModel):
    name: str = Field(..., description="Competitor company name")
    website: Optional[str] = Field(None, description="Company website")
    description: str = Field(..., description="Company description")
    business_model: str = Field(..., description="Business model")
    target_market: str = Field(..., description="Target market")
    industry: Optional[str] = Field(None, description="Industry sector")
    founding_year: Optional[int] = Field(None, description="Year founded")
    headquarters: Optional[str] = Field(None, description="Headquarters location")
    employee_count: Optional[str] = Field(None, description="Number of employees")
    funding_info: Optional[Dict[str, Any]] = Field(None, description="Funding information")
    key_products: List[str] = Field(default_factory=list, description="Key products/services")
    pricing_strategy: Optional[str] = Field(None, description="Pricing strategy")
    market_position: Optional[str] = Field(None, description="Market position")
    strengths: List[str] = Field(default_factory=list, description="Company strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Company weaknesses")
    recent_news: List[Dict[str, Any]] = Field(default_factory=list, description="Recent news and updates")
    social_media_presence: Dict[str, str] = Field(default_factory=dict, description="Social media links")
    financial_data: Optional[Dict[str, Any]] = Field(None, description="Financial information")
    technology_stack: List[str] = Field(default_factory=list, description="Technology stack")
    partnerships: List[str] = Field(default_factory=list, description="Key partnerships")
    competitive_advantages: List[str] = Field(default_factory=list, description="Competitive advantages")
    market_share: Optional[float] = Field(None, description="Market share percentage")
    growth_trajectory: Optional[str] = Field(None, description="Growth trajectory analysis")
    threat_level: Optional[str] = Field(None, description="Threat level to client")
    
    # Product-specific fields
    primary_product: Optional[str] = Field(None, description="Primary product being compared")
    product_details: Optional[Dict[str, Any]] = Field(None, description="Detailed product information")
    product_features: List[str] = Field(default_factory=list, description="Key product features")
    product_pricing: Optional[Dict[str, Any]] = Field(None, description="Product pricing information")
    product_reviews: Optional[Dict[str, Any]] = Field(None, description="Product review aggregation")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisResult(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    request_id: str = Field(..., description="Original request ID")
    client_company: str = Field(..., description="Client company name")
    industry: str = Field(..., description="Industry sector")
    target_market: Optional[str] = Field(None, description="Target market from original request")
    business_model: Optional[str] = Field(None, description="Business model from original request")
    specific_requirements: Optional[str] = Field(None, description="Specific requirements from original request")
    max_competitors: Optional[int] = Field(None, description="Max competitors from original request")
    competitors: List[CompetitorData] = Field(default_factory=list, description="List of competitor data")
    market_analysis: Dict[str, Any] = Field(default_factory=dict, description="Market analysis results")
    competitive_landscape: Dict[str, Any] = Field(default_factory=dict, description="Competitive landscape overview")
    threats_opportunities: Dict[str, Any] = Field(default_factory=dict, description="Threats and opportunities")
    recommendations: List[str] = Field(default_factory=list, description="Strategic recommendations")
    status: str = Field(default="pending", description="Analysis status")
    current_stage: Optional[str] = Field(None, description="Current workflow stage")
    progress: int = Field(default=0, description="Analysis progress percentage")
    quality_review: Optional[QualityReview] = Field(None, description="Quality review data")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }
        allow_population_by_field_name = True


class AnalysisMetrics(BaseModel):
    total_competitors_found: int = 0
    data_sources_used: List[str] = Field(default_factory=list)
    analysis_duration_seconds: Optional[float] = None
    confidence_score: Optional[float] = None
    data_quality_score: Optional[float] = None
    completeness_score: Optional[float] = None