from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    """Individual report section"""
    title: str = Field(..., description="Section title")
    content: Dict[str, Any] = Field(..., description="Section content data")
    summary: str = Field(..., description="Section summary")


class Report(BaseModel):
    """Complete analysis report"""
    id: Optional[str] = Field(None, alias="_id")
    analysis_id: str = Field(..., description="Associated analysis ID")
    title: str = Field(..., description="Report title")
    executive_summary: str = Field(..., description="Executive summary")
    client_company: str = Field(..., description="Client company name")
    industry: str = Field(..., description="Industry sector")
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Report sections
    market_overview: Dict[str, Any] = Field(..., description="Market overview section")
    competitive_landscape: Dict[str, Any] = Field(..., description="Competitive landscape analysis")
    competitor_profiles: List[Dict[str, Any]] = Field(default_factory=list, description="Individual competitor profiles")
    swot_analysis: Dict[str, Any] = Field(default_factory=dict, description="SWOT analysis")
    market_positioning: Dict[str, Any] = Field(default_factory=dict, description="Market positioning analysis")
    threats_opportunities: Dict[str, Any] = Field(default_factory=dict, description="Threats and opportunities")
    strategic_recommendations: Dict[str, Any] = Field(..., description="Strategic recommendations")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True  # Updated for Pydantic v2