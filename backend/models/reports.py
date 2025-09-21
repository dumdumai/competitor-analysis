from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .analysis import CompetitorData


class ReportSection(BaseModel):
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    subsections: List["ReportSection"] = Field(default_factory=list, description="Nested subsections")
    charts: List[Dict[str, Any]] = Field(default_factory=list, description="Chart data for visualization")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Table data")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from this section")


class Report(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    analysis_id: str = Field(..., description="Associated analysis ID")
    title: str = Field(..., description="Report title")
    executive_summary: str = Field(..., description="Executive summary")
    client_company: str = Field(..., description="Client company name")
    industry: str = Field(..., description="Industry sector")
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Main sections
    market_overview: ReportSection = Field(..., description="Market overview section")
    competitive_landscape: ReportSection = Field(..., description="Competitive landscape analysis")
    competitor_profiles: List[ReportSection] = Field(default_factory=list, description="Individual competitor profiles")
    swot_analysis: ReportSection = Field(..., description="SWOT analysis")
    market_positioning: ReportSection = Field(..., description="Market positioning analysis")
    threats_opportunities: ReportSection = Field(..., description="Threats and opportunities")
    strategic_recommendations: ReportSection = Field(..., description="Strategic recommendations")
    
    # Metadata
    total_competitors_analyzed: int = Field(default=0)
    data_sources: List[str] = Field(default_factory=list)
    confidence_level: str = Field(default="medium", description="Overall confidence level")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        allow_population_by_field_name = True


# Update the forward reference
ReportSection.model_rebuild()