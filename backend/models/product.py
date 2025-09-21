from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class ProductFeature(BaseModel):
    name: str = Field(..., description="Feature name")
    description: str = Field(..., description="Feature description")
    category: str = Field(..., description="Feature category (core, advanced, optional)")
    availability: str = Field(default="available", description="Feature availability status")


class PricingTier(BaseModel):
    name: str = Field(..., description="Pricing tier name (e.g., Basic, Pro, Enterprise)")
    price: Optional[float] = Field(None, description="Price in USD")
    billing_cycle: Optional[str] = Field(None, description="Billing cycle (monthly, yearly, one-time)")
    features: List[str] = Field(default_factory=list, description="Features included in this tier")
    limitations: Dict[str, Any] = Field(default_factory=dict, description="Usage limitations")
    target_audience: str = Field(..., description="Target audience for this tier")


class ProductData(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(..., description="Product name")
    company: str = Field(..., description="Company that owns the product")
    category: str = Field(..., description="Product category")
    sub_category: Optional[str] = Field(None, description="Product sub-category")
    description: str = Field(..., description="Product description")
    target_audience: str = Field(..., description="Primary target audience")
    launch_date: Optional[datetime] = Field(None, description="Product launch date")
    version: Optional[str] = Field(None, description="Current product version")
    website_url: Optional[str] = Field(None, description="Product website URL")
    documentation_url: Optional[str] = Field(None, description="Product documentation URL")
    
    # Features
    core_features: List[ProductFeature] = Field(default_factory=list, description="Core product features")
    unique_features: List[str] = Field(default_factory=list, description="Unique selling points")
    integrations: List[str] = Field(default_factory=list, description="Available integrations")
    supported_platforms: List[str] = Field(default_factory=list, description="Supported platforms")
    
    # Pricing
    pricing_model: str = Field(..., description="Pricing model (subscription, one-time, freemium, usage-based)")
    pricing_tiers: List[PricingTier] = Field(default_factory=list, description="Available pricing tiers")
    free_trial: bool = Field(default=False, description="Whether free trial is available")
    free_trial_duration: Optional[int] = Field(None, description="Free trial duration in days")
    
    # Performance & Technical
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance benchmarks")
    technology_stack: List[str] = Field(default_factory=list, description="Technology stack used")
    api_availability: bool = Field(default=False, description="Whether API is available")
    mobile_app: bool = Field(default=False, description="Whether mobile app is available")
    
    # Market Position
    market_share: Optional[float] = Field(None, description="Market share percentage")
    user_base_size: Optional[str] = Field(None, description="Size of user base")
    customer_segments: List[str] = Field(default_factory=list, description="Customer segments served")
    geographic_availability: List[str] = Field(default_factory=list, description="Geographic markets served")
    
    # Reviews & Ratings
    average_rating: Optional[float] = Field(None, description="Average user rating")
    total_reviews: Optional[int] = Field(None, description="Total number of reviews")
    review_sources: Dict[str, float] = Field(default_factory=dict, description="Ratings from different sources")
    customer_satisfaction_score: Optional[float] = Field(None, description="Customer satisfaction score")
    
    # Competitive Analysis
    strengths: List[str] = Field(default_factory=list, description="Product strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Product weaknesses")
    opportunities: List[str] = Field(default_factory=list, description="Market opportunities")
    threats: List[str] = Field(default_factory=list, description="Competitive threats")
    competitive_advantages: List[str] = Field(default_factory=list, description="Key competitive advantages")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    data_sources: List[str] = Field(default_factory=list, description="Sources of product information")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }
        allow_population_by_field_name = True


class ProductComparisonRequest(BaseModel):
    client_product: str = Field(..., description="Name of the client's product")
    client_company: str = Field(..., description="Name of the client company")
    product_category: str = Field(..., description="Product category for comparison")
    comparison_criteria: List[str] = Field(
        default_factory=lambda: ["features", "pricing", "performance", "market_position", "user_reviews"],
        description="Criteria for comparison"
    )
    target_market: str = Field(..., description="Target market or geographic region")
    specific_requirements: Optional[str] = Field(None, description="Specific comparison requirements")
    max_products: int = Field(default=10, description="Maximum number of products to compare")
    include_indirect_competitors: bool = Field(default=True, description="Include indirect competitors")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProductComparison(BaseModel):
    product_a: ProductData = Field(..., description="First product in comparison")
    product_b: ProductData = Field(..., description="Second product in comparison")
    
    # Feature Comparison
    common_features: List[str] = Field(default_factory=list, description="Features present in both products")
    unique_to_a: List[str] = Field(default_factory=list, description="Features unique to product A")
    unique_to_b: List[str] = Field(default_factory=list, description="Features unique to product B")
    feature_advantage: str = Field(..., description="Which product has feature advantage and why")
    
    # Pricing Comparison
    price_comparison: Dict[str, Any] = Field(default_factory=dict, description="Price comparison across tiers")
    value_for_money: str = Field(..., description="Which product offers better value and why")
    
    # Performance Comparison
    performance_comparison: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics comparison")
    performance_winner: str = Field(..., description="Which product performs better overall")
    
    # Market Position Comparison
    market_position_analysis: str = Field(..., description="Comparative market position analysis")
    growth_trajectory_comparison: str = Field(..., description="Growth trajectory comparison")
    
    # Overall Assessment
    overall_winner: str = Field(..., description="Overall winner and reasoning")
    recommendation: str = Field(..., description="Strategic recommendation based on comparison")
    key_differentiators: List[str] = Field(default_factory=list, description="Key differentiating factors")
    
    # Metadata
    comparison_date: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(..., description="Confidence in comparison accuracy")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProductComparisonResult(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    request_id: str = Field(..., description="Original request ID")
    client_product: ProductData = Field(..., description="Client product data")
    competitor_products: List[ProductData] = Field(default_factory=list, description="Competitor products")
    comparisons: List[ProductComparison] = Field(default_factory=list, description="Individual comparisons")
    
    # Market Analysis
    market_overview: Dict[str, Any] = Field(default_factory=dict, description="Product market overview")
    category_trends: List[str] = Field(default_factory=list, description="Product category trends")
    innovation_analysis: Dict[str, Any] = Field(default_factory=dict, description="Innovation trends in the category")
    
    # Competitive Positioning
    competitive_matrix: Dict[str, Any] = Field(default_factory=dict, description="Competitive positioning matrix")
    market_gaps: List[str] = Field(default_factory=list, description="Identified market gaps")
    differentiation_opportunities: List[str] = Field(default_factory=list, description="Differentiation opportunities")
    
    # Strategic Recommendations
    product_improvements: List[str] = Field(default_factory=list, description="Recommended product improvements")
    pricing_recommendations: List[str] = Field(default_factory=list, description="Pricing strategy recommendations")
    feature_roadmap_suggestions: List[str] = Field(default_factory=list, description="Feature roadmap suggestions")
    go_to_market_recommendations: List[str] = Field(default_factory=list, description="Go-to-market recommendations")
    
    # Metadata
    status: str = Field(default="pending", description="Analysis status")
    progress: int = Field(default=0, description="Analysis progress percentage")
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