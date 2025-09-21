from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from loguru import logger

from models.reports import Report
from database.repositories import ReportRepository, AnalysisRepository


router = APIRouter()


def get_report_repository(request: Request) -> ReportRepository:
    """Dependency to get report repository from app state"""
    return request.app.state.report_repository


def get_analysis_repository(request: Request) -> AnalysisRepository:
    """Dependency to get analysis repository from app state"""
    return request.app.state.analysis_repository


@router.get("/reports", response_model=List[Report])
async def list_reports(
    client_company: Optional[str] = None,
    limit: int = 50,
    report_repository: ReportRepository = Depends(get_report_repository)
):
    """
    List all generated reports with optional filtering
    
    Parameters:
    - client_company: Filter by client company name (partial match)
    - limit: Maximum number of results to return (default: 50)
    """
    try:
        if limit > 100:
            limit = 100  # Cap at 100 for performance
        
        reports = await report_repository.list_reports(
            client_company=client_company,
            limit=limit
        )
        
        return reports
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to list reports")


@router.get("/reports/{report_id}", response_model=Report)
async def get_report(
    report_id: str,
    report_repository: ReportRepository = Depends(get_report_repository)
):
    """
    Get a specific report by its ID
    
    Returns the complete report including all sections, charts, and insights.
    """
    try:
        report = await report_repository.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail="Failed to get report")


@router.get("/analysis/{analysis_id}/report", response_model=Report)
async def get_report_by_analysis(
    analysis_id: str,
    report_repository: ReportRepository = Depends(get_report_repository)
):
    """
    Get the report associated with a specific analysis
    
    Returns the report generated for the given analysis ID.
    """
    try:
        report = await report_repository.get_report_by_analysis(analysis_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found for this analysis")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report by analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get report")


@router.post("/analysis/{analysis_id}/generate-report")
async def generate_report(
    analysis_id: str,
    analysis_repository: AnalysisRepository = Depends(get_analysis_repository),
    report_repository: ReportRepository = Depends(get_report_repository)
):
    """
    Generate a new report for an existing analysis
    
    This endpoint allows regenerating reports with updated formatting or
    creating reports for analyses that were completed without report generation.
    """
    try:
        # Check if analysis exists and is completed
        analysis = await analysis_repository.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis.status != "completed":
            raise HTTPException(
                status_code=400, 
                detail="Cannot generate report for incomplete analysis"
            )
        
        # Check if report already exists
        existing_report = await report_repository.get_report_by_analysis(analysis_id)
        if existing_report:
            raise HTTPException(
                status_code=409, 
                detail="Report already exists for this analysis"
            )
        
        # TODO: Implement report generation logic
        # This would involve creating a report from the analysis data
        # For now, return a placeholder response
        
        return {
            "message": "Report generation initiated",
            "analysis_id": analysis_id,
            "status": "generating"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/reports/{report_id}/executive-summary")
async def get_report_executive_summary(
    report_id: str,
    report_repository: ReportRepository = Depends(get_report_repository)
):
    """
    Get only the executive summary from a report
    
    Returns just the executive summary section for quick overview.
    """
    try:
        report = await report_repository.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "report_id": report_id,
            "title": report.title,
            "client_company": report.client_company,
            "industry": report.industry,
            "executive_summary": report.executive_summary,
            "analysis_date": report.analysis_date,
            "confidence_level": report.confidence_level
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting executive summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get executive summary")


@router.get("/reports/{report_id}/sections/{section_name}")
async def get_report_section(
    report_id: str,
    section_name: str,
    report_repository: ReportRepository = Depends(get_report_repository)
):
    """
    Get a specific section from a report
    
    Available sections:
    - market_overview
    - competitive_landscape
    - swot_analysis
    - market_positioning
    - threats_opportunities
    - strategic_recommendations
    """
    try:
        report = await report_repository.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Map section names to report attributes
        section_mapping = {
            "market_overview": report.market_overview,
            "competitive_landscape": report.competitive_landscape,
            "swot_analysis": report.swot_analysis,
            "market_positioning": report.market_positioning,
            "threats_opportunities": report.threats_opportunities,
            "strategic_recommendations": report.strategic_recommendations
        }
        
        if section_name not in section_mapping:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid section name. Available sections: {list(section_mapping.keys())}"
            )
        
        section = section_mapping[section_name]
        
        return {
            "report_id": report_id,
            "section_name": section_name,
            "section": section,
            "client_company": report.client_company
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report section: {e}")
        raise HTTPException(status_code=500, detail="Failed to get report section")


@router.get("/reports/{report_id}/competitor-profiles")
async def get_report_competitor_profiles(
    report_id: str,
    report_repository: ReportRepository = Depends(get_report_repository)
):
    """
    Get all competitor profiles from a report
    
    Returns the individual competitor profile sections.
    """
    try:
        report = await report_repository.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "report_id": report_id,
            "client_company": report.client_company,
            "competitor_profiles": report.competitor_profiles,
            "total_competitors": len(report.competitor_profiles)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting competitor profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get competitor profiles")


@router.get("/reports/statistics")
async def get_report_statistics(
    report_repository: ReportRepository = Depends(get_report_repository)
):
    """
    Get overall statistics about reports
    
    Returns aggregate statistics about all reports in the system.
    """
    try:
        # Get all reports (this could be optimized with database aggregation)
        reports = await report_repository.list_reports(limit=1000)
        
        # Calculate statistics
        total_reports = len(reports)
        
        # Industry distribution
        industries = {}
        confidence_levels = {}
        companies = set()
        
        for report in reports:
            # Industry stats
            industry = report.industry
            industries[industry] = industries.get(industry, 0) + 1
            
            # Confidence level stats
            confidence = report.confidence_level
            confidence_levels[confidence] = confidence_levels.get(confidence, 0) + 1
            
            # Unique companies
            companies.add(report.client_company)
        
        # Get recent reports (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_reports = [
            r for r in reports 
            if r.created_at and r.created_at >= thirty_days_ago
        ]
        
        return {
            "total_reports": total_reports,
            "unique_companies": len(companies),
            "recent_reports_30_days": len(recent_reports),
            "industry_distribution": industries,
            "confidence_distribution": confidence_levels,
            "average_competitors_per_report": (
                sum(r.total_competitors_analyzed for r in reports) / total_reports
                if total_reports > 0 else 0
            )
        }
        
    except Exception as e:
        logger.error(f"Error getting report statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get report statistics")