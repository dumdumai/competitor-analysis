import asyncio
import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

from models.analysis import AnalysisRequest, AnalysisResult
from models.agent_state import HumanReviewDecision
from agents.coordinator import CompetitorAnalysisCoordinator
from database.repositories import AnalysisRepository


router = APIRouter()


def get_coordinator(request: Request) -> CompetitorAnalysisCoordinator:
    """Dependency to get coordinator from app state"""
    return request.app.state.coordinator


def get_analysis_repository(request: Request) -> AnalysisRepository:
    """Dependency to get analysis repository from app state"""
    return request.app.state.analysis_repository


@router.post("/analysis", response_model=dict)
async def start_analysis(
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    coordinator: CompetitorAnalysisCoordinator = Depends(get_coordinator)
):
    """
    Start a new competitor analysis
    
    This endpoint initiates a comprehensive competitor analysis workflow that includes:
    - Client requirement processing
    - Competitor discovery
    - Data collection and processing
    - Quality assurance
    - Market analysis
    - Competitive analysis
    - Report generation
    
    The analysis runs asynchronously in the background.
    """
    try:
        logger.info(f"Starting analysis for {analysis_request.client_company}")
        
        # Validate request
        if not analysis_request.client_company.strip():
            raise HTTPException(status_code=400, detail="Client company name is required")
        
        if not analysis_request.industry.strip():
            raise HTTPException(status_code=400, detail="Industry is required")
        
        if analysis_request.max_competitors < 1 or analysis_request.max_competitors > 50:
            raise HTTPException(
                status_code=400, 
                detail="Max competitors must be between 1 and 50"
            )
        
        # Create the analysis record first to get the request_id
        request_id = await coordinator.analysis_repository.create_analysis(analysis_request)
        
        # Start analysis workflow in background with the request_id
        background_tasks.add_task(run_analysis_workflow, coordinator, analysis_request, request_id)
        
        return {
            "message": "Analysis started successfully",
            "request_id": request_id,
            "status": "initiated",
            "client_company": analysis_request.client_company,
            "industry": analysis_request.industry,
            "estimated_duration": "15-30 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analysis")


async def run_analysis_workflow(
    coordinator: CompetitorAnalysisCoordinator, 
    analysis_request: AnalysisRequest,
    request_id: str
):
    """Background task to run the analysis workflow"""
    try:
        await coordinator.analyze_competitors_with_id(analysis_request, request_id)
        logger.info(f"Analysis workflow completed successfully: {request_id}")
    except Exception as e:
        logger.error(f"Analysis workflow failed: {e}")
        # Update analysis status to failed
        try:
            await coordinator.analysis_repository.update_analysis(
                request_id, {
                    "status": "failed",
                    "progress": 100,
                    "error_message": str(e)
                }
            )
        except Exception as update_error:
            logger.error(f"Failed to update analysis status: {update_error}")


@router.get("/analysis/{request_id}/progress")
async def get_analysis_progress(
    request_id: str,
    coordinator: CompetitorAnalysisCoordinator = Depends(get_coordinator),
    request: Request = None
):
    """Get real-time progress of an analysis"""
    try:
        redis_service = request.app.state.redis_service
        
        # Get progress data from Redis
        progress_data = await redis_service.get_analysis_progress(request_id)
        progress_message = await redis_service.get_progress_message(request_id)
        
        # Get analysis status from database
        analysis_repository = request.app.state.analysis_repository
        analysis = await analysis_repository.get_analysis(request_id)
        
        current_stage = 'initializing'
        status = 'pending'
        
        if analysis:
            status = analysis.status
            current_stage = getattr(analysis, 'current_stage', 'initializing')
        
        # If no current stage from database, try to get from agent state
        if current_stage == 'initializing':
            agent_state = await coordinator.get_agent_state(request_id)
            if agent_state:
                # Determine current stage from agent state
                if getattr(agent_state, 'report_generated', False):
                    current_stage = 'report'
                elif hasattr(agent_state, 'retry_context') and agent_state.retry_context and agent_state.retry_context.awaiting_human_review:
                    current_stage = 'human_review'
                elif getattr(agent_state, 'quality_scores', None):
                    current_stage = 'quality'
                elif getattr(agent_state, 'processed_data', None) and agent_state.processed_data.get('recommendations'):
                    current_stage = 'analysis'
                elif getattr(agent_state, 'search_results', None):
                    current_stage = 'search'
        
        return {
            "request_id": request_id,
            "current_stage": current_stage,
            "status": status,
            "progress": progress_data.get('progress', 0) if progress_data else 0,
            "message": progress_message or (progress_data.get('message', '') if progress_data else '')
        }
        
    except Exception as e:
        logger.error(f"Error getting progress for {request_id}: {e}")
        return {
            "request_id": request_id,
            "current_stage": "unknown",
            "status": "unknown",
            "progress": 0,
            "message": ""
        }


@router.get("/analysis/{request_id}/status")
async def get_analysis_status(
    request_id: str,
    coordinator: CompetitorAnalysisCoordinator = Depends(get_coordinator)
):
    """
    Get the current status of an analysis
    
    Returns real-time status information including:
    - Current progress percentage
    - Current stage being executed
    - Completed stages
    - Any errors or warnings
    """
    try:
        status = await coordinator.get_analysis_status(request_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis status")


@router.get("/analysis/{request_id}", response_model=AnalysisResult)
async def get_analysis_result(
    request_id: str,
    analysis_repository: AnalysisRepository = Depends(get_analysis_repository),
    coordinator: CompetitorAnalysisCoordinator = Depends(get_coordinator)
):
    """
    Get the complete analysis result
    
    Returns the full analysis including:
    - Competitor data
    - Market analysis
    - Competitive landscape
    - Threats and opportunities
    - Strategic recommendations
    
    For analyses in human review stage, enriches data from agent state if main record is empty.
    """
    try:
        analysis = await analysis_repository.get_analysis(request_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # If analysis is in human review stage and has empty data, enrich from agent state
        if (analysis.current_stage == 'human_review' and 
            (not analysis.competitors or len(analysis.competitors) == 0)):
            
            try:
                logger.info(f"Enriching analysis data from agent state for {request_id}")
                agent_state = await coordinator.get_agent_state(request_id)
                
                if agent_state:
                    # Map agent state data to analysis format
                    if agent_state.competitor_data and len(agent_state.competitor_data) > 0:
                        analysis.competitors = [comp.dict() for comp in agent_state.competitor_data]
                    
                    if agent_state.market_insights and agent_state.market_insights.get('market_analysis'):
                        analysis.market_analysis = agent_state.market_insights['market_analysis']
                    
                    if agent_state.recommendations and len(agent_state.recommendations) > 0:
                        analysis.recommendations = agent_state.recommendations
                    
                    if agent_state.competitive_analysis:
                        # Map competitive analysis data
                        comp_analysis = agent_state.competitive_analysis
                        if comp_analysis.get('positioning'):
                            analysis.competitive_positioning = comp_analysis['positioning']
                        
                        # Map threats and opportunities if available
                        if hasattr(agent_state, 'market_insights') and agent_state.market_insights:
                            market_data = agent_state.market_insights.get('market_analysis', {}).get('market_data', {})
                            if market_data.get('opportunities') or market_data.get('threats'):
                                analysis.threats_opportunities = {
                                    'opportunities': market_data.get('opportunities', []),
                                    'threats': market_data.get('threats', [])
                                }
                    
                    logger.info(f"Successfully enriched analysis data with {len(analysis.competitors)} competitors")
                
            except Exception as e:
                logger.warning(f"Could not enrich analysis data from agent state: {e}")
                # Continue with original analysis even if enrichment fails
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis result: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis result")


@router.get("/analysis", response_model=List[AnalysisResult])
async def list_analyses(
    client_company: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    analysis_repository: AnalysisRepository = Depends(get_analysis_repository)
):
    """
    List all analyses with optional filtering
    
    Parameters:
    - client_company: Filter by client company name (partial match)
    - status: Filter by analysis status (pending, in_progress, completed, failed)
    - limit: Maximum number of results to return (default: 50)
    """
    try:
        if limit > 100:
            limit = 100  # Cap at 100 for performance
        
        analyses = await analysis_repository.list_analyses(
            client_company=client_company,
            status=status,
            limit=limit
        )
        
        return analyses
        
    except Exception as e:
        logger.error(f"Error listing analyses: {e}")
        raise HTTPException(status_code=500, detail="Failed to list analyses")


@router.post("/analysis/{request_id}/restart")
async def restart_analysis(
    request_id: str,
    background_tasks: BackgroundTasks,
    coordinator: CompetitorAnalysisCoordinator = Depends(get_coordinator),
    analysis_repository: AnalysisRepository = Depends(get_analysis_repository)
):
    """
    Restart a completed or failed analysis
    
    This endpoint restarts an analysis with the same parameters.
    """
    try:
        logger.info(f"Restarting analysis {request_id}")
        
        # Get the original analysis
        original_analysis = await analysis_repository.get_analysis(request_id)
        if not original_analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Create a new analysis request with the same parameters
        analysis_request = AnalysisRequest(
            client_company=original_analysis.client_company,
            industry=original_analysis.industry,
            target_market=original_analysis.target_market,
            business_model=getattr(original_analysis, 'business_model', 'B2B'),  # Default to B2B if not present
            specific_requirements=original_analysis.specific_requirements,
            max_competitors=getattr(original_analysis, 'max_competitors', 10),  # Default to 10 if not present
            comparison_type=getattr(original_analysis, 'comparison_type', 'company'),
            client_product=getattr(original_analysis, 'client_product', None),
            product_category=getattr(original_analysis, 'product_category', None),
            comparison_criteria=getattr(original_analysis, 'comparison_criteria', [])
        )
        
        # Create analysis in database and get the new request ID
        new_request_id = await analysis_repository.create_analysis(analysis_request)
        
        # Start the new analysis with the generated ID
        background_tasks.add_task(
            coordinator.analyze_competitors_with_id,
            analysis_request,
            new_request_id
        )
        
        return {
            "request_id": new_request_id,
            "original_request_id": request_id,
            "message": "Analysis restarted successfully",
            "status": "started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to restart analysis")


@router.delete("/analysis/{request_id}")
async def delete_analysis(
    request_id: str,
    analysis_repository: AnalysisRepository = Depends(get_analysis_repository),
    request: Request = None
):
    """
    Delete an analysis and its associated data
    
    This will remove the analysis from the database and clear any cached data.
    This action cannot be undone.
    """
    try:
        # Check if analysis exists
        analysis = await analysis_repository.get_analysis(request_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Only allow deletion of completed or failed analyses
        if analysis.status in ["in_progress", "pending"]:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete analysis that is still in progress"
            )
        
        # Clear from cache
        redis_service = request.app.state.redis_service
        await redis_service.delete_agent_state(request_id)
        
        # Note: In a full implementation, you would also delete from database
        # For now, we'll just clear the cache
        
        return {
            "message": "Analysis deleted successfully",
            "request_id": request_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete analysis")


@router.get("/analysis/{request_id}/competitors")
async def get_analysis_competitors(
    request_id: str,
    analysis_repository: AnalysisRepository = Depends(get_analysis_repository)
):
    """
    Get only the competitor data from an analysis
    
    Returns a simplified view of just the competitor information
    without the full analysis details.
    """
    try:
        analysis = await analysis_repository.get_analysis(request_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "request_id": request_id,
            "client_company": analysis.client_company,
            "industry": analysis.industry,
            "competitors": analysis.competitors,
            "total_competitors": len(analysis.competitors),
            "analysis_date": analysis.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis competitors: {e}")
        raise HTTPException(status_code=500, detail="Failed to get competitors")


@router.get("/analysis/{request_id}/recommendations")
async def get_analysis_recommendations(
    request_id: str,
    analysis_repository: AnalysisRepository = Depends(get_analysis_repository)
):
    """
    Get only the strategic recommendations from an analysis
    
    Returns just the strategic recommendations without other analysis data.
    """
    try:
        analysis = await analysis_repository.get_analysis(request_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "request_id": request_id,
            "client_company": analysis.client_company,
            "recommendations": analysis.recommendations,
            "total_recommendations": len(analysis.recommendations),
            "analysis_date": analysis.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.get("/analysis/{request_id}/search-logs")
async def get_analysis_search_logs(
    request_id: str,
    coordinator: CompetitorAnalysisCoordinator = Depends(get_coordinator)
):
    """
    Get detailed search logs for debugging and transparency
    
    Returns all Tavily search queries, parameters, and results for the analysis.
    This helps users understand exactly what searches were performed and debug results.
    """
    try:
        # Get the agent state which contains search logs
        agent_state = await coordinator.get_agent_state(request_id)
        
        if not agent_state:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "request_id": request_id,
            "client_company": agent_state.analysis_context.client_company,
            "industry": agent_state.analysis_context.industry,
            "search_logs": agent_state.search_logs,
            "total_searches": len(agent_state.search_logs),
            "search_summary": {
                "by_type": {},
                "total_results": 0,
                "failed_searches": 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting search logs for {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search logs")


# Human-in-the-loop endpoints for quality review

@router.get("/analysis/{request_id}/quality-review")
async def get_quality_review(
    request_id: str,
    request: Request
):
    """
    Get quality review data for human inspection
    
    Returns quality issues identified by the quality agent that require human review.
    This endpoint is called when the workflow is paused for human review.
    """
    try:
        # First check database for persistent quality review data
        analysis_repository = request.app.state.analysis_repository
        analysis = await analysis_repository.get_analysis(request_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Check if we have quality review data in the database
        if analysis.quality_review and analysis.quality_review.quality_issues:
            # Convert database model to API response format
            review_data = {
                "request_id": request_id,
                "quality_issues": [issue.dict() for issue in analysis.quality_review.quality_issues],
                "current_analysis": {
                    "competitors_found": len(analysis.competitors),
                    "quality_scores": analysis.quality_review.quality_scores,
                    "average_quality": analysis.quality_review.average_quality_score,
                    "analysis_completed": analysis.current_stage in ["quality", "human_review", "completed"]
                },
                "available_actions": [
                    {"id": "proceed", "label": "Proceed with current results", "description": "Continue to report generation"},
                    {"id": "retry_search", "label": "Retry search", "description": "Re-run competitor discovery and data collection"},
                    {"id": "retry_analysis", "label": "Retry analysis", "description": "Re-run market and competitive analysis"},
                    {"id": "modify_params", "label": "Modify parameters", "description": "Adjust analysis parameters and retry"},
                    {"id": "abort", "label": "Abort analysis", "description": "Stop the analysis workflow"}
                ]
            }
            return review_data
        
        # Fallback to agent state for active reviews
        if analysis.status == "in_progress" and analysis.current_stage == "human_review":
            try:
                coordinator = request.app.state.coordinator
                agent_state = await coordinator.get_agent_state(request_id)
                
                if agent_state:
                    # Extract quality data from agent state
                    quality_issues = []
                    
                    if (hasattr(agent_state, 'retry_context') and 
                        agent_state.retry_context and 
                        hasattr(agent_state.retry_context, 'quality_feedback')):
                        quality_issues = [issue.dict() for issue in agent_state.retry_context.quality_feedback]
                    
                    competitors_count = len(agent_state.competitor_data) if agent_state.competitor_data else 0
                    quality_scores = agent_state.quality_scores if hasattr(agent_state, 'quality_scores') else {}
                    
                    # Calculate average quality score
                    avg_quality = 0
                    if quality_scores:
                        avg_quality = sum(quality_scores.values()) / len(quality_scores)
                    
                    review_data = {
                        "request_id": request_id,
                        "quality_issues": quality_issues,
                        "current_analysis": {
                            "competitors_found": competitors_count,
                            "quality_scores": quality_scores,
                            "average_quality": avg_quality,
                            "analysis_completed": True
                        },
                        "available_actions": [
                            {"id": "proceed", "label": "Proceed with current results", "description": "Continue to report generation"},
                            {"id": "retry_search", "label": "Retry search", "description": "Re-run competitor discovery and data collection"},
                            {"id": "retry_analysis", "label": "Retry analysis", "description": "Re-run market and competitive analysis"},
                            {"id": "modify_params", "label": "Modify parameters", "description": "Adjust analysis parameters and retry"},
                            {"id": "abort", "label": "Abort analysis", "description": "Stop the analysis workflow"}
                        ]
                    }
                else:
                    # No agent state found - return empty data
                    review_data = {
                        "request_id": request_id,
                        "quality_issues": [],
                        "current_analysis": {
                            "competitors_found": len(analysis.competitors),
                            "quality_scores": {},
                            "average_quality": 0,
                            "analysis_completed": True
                        },
                        "available_actions": []
                    }
            except Exception as e:
                logger.warning(f"Could not load agent state for quality review: {e}")
                # Fallback to Redis if agent state fails
                redis_service = request.app.state.redis_service
                review_data = await redis_service.get_human_review_data(request_id)
                
                if not review_data:
                    review_data = {
                        "request_id": request_id,
                        "quality_issues": [],
                        "current_analysis": {
                            "competitors_found": len(analysis.competitors),
                            "quality_scores": {},
                            "average_quality": 0,
                            "analysis_completed": True
                        },
                        "available_actions": []
                    }
        else:
            raise HTTPException(
                status_code=400, 
                detail="Analysis is not currently awaiting human review"
            )
        
        return review_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quality review for {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quality review data")


@router.post("/analysis/{request_id}/quality-review/decision")
async def submit_quality_decision(
    request_id: str,
    decision: HumanReviewDecision,
    request: Request
):
    """
    Submit human decision on quality issues
    
    This endpoint receives the human decision and resumes the workflow.
    The decision can be to proceed, retry agents, modify parameters, or abort.
    """
    try:
        logger.info(f"Received quality decision for {request_id}: {decision}")
        
        coordinator = request.app.state.coordinator
        redis_service = request.app.state.redis_service
        
        # Get current agent state
        agent_state = await coordinator.get_agent_state(request_id)
        if not agent_state:
            logger.error(f"No agent state found for request_id: {request_id}")
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        logger.info(f"Agent state found. Current status: awaiting_review={agent_state.is_awaiting_human_review()}")
        
        # Verify that analysis is waiting for human review
        # Check both the cached state and database current_stage as a fallback
        is_awaiting_review = agent_state.is_awaiting_human_review()
        
        if not is_awaiting_review:
            # Fallback: check database current_stage
            try:
                analysis = await get_analysis_repository(request).get_analysis(request_id)
                if analysis and getattr(analysis, 'current_stage', None) == 'human_review':
                    logger.info(f"✅ Fallback check: Database shows current_stage=human_review for {request_id}")
                    is_awaiting_review = True
                    # Update the cached state to be consistent
                    agent_state.set_awaiting_human_review(True)
                    await redis_service.cache_agent_state(request_id, agent_state.dict())
                    logger.info(f"🔧 Updated cached state to awaiting_human_review=True for {request_id}")
            except Exception as e:
                logger.warning(f"Failed to check database current_stage: {e}")
        
        if not is_awaiting_review:
            logger.error(f"Analysis {request_id} is not awaiting human review. Current state: {agent_state.retry_context}")
            raise HTTPException(
                status_code=400, 
                detail="Analysis is not currently awaiting human review"
            )
        
        # Validate decision
        valid_decisions = ["proceed", "retry_search", "retry_analysis", "modify_params", "abort"]
        logger.info(f"Validating decision: '{decision.decision}' against valid options: {valid_decisions}")
        if decision.decision not in valid_decisions:
            logger.error(f"Invalid decision received: '{decision.decision}'. Valid options: {valid_decisions}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid decision. Must be one of: {valid_decisions}"
            )
        
        # Set the human decision in the state
        agent_state.set_human_decision(decision)
        
        # Save updated state
        await coordinator._save_intermediate_state(agent_state)
        
        # Also persist the decision to the database
        try:
            analysis_repository = request.app.state.analysis_repository
            analysis = await analysis_repository.get_analysis(request_id)
            if analysis and analysis.quality_review:
                # Update the quality review with the human decision
                from models.analysis import HumanReviewDecision as DBHumanReviewDecision
                from datetime import datetime
                
                db_decision = DBHumanReviewDecision(
                    decision=decision.decision,
                    feedback=decision.feedback,
                    modified_params=decision.modified_params,
                    selected_issues=decision.selected_issues,
                    reviewed_at=datetime.utcnow()
                )
                
                await analysis_repository.update_analysis(
                    request_id, {
                        "quality_review.review_decision": db_decision.dict(),
                        "quality_review.completed_at": datetime.utcnow()
                    }
                )
                logger.info(f"✅ Human decision persisted to database for {request_id}")
        except Exception as e:
            logger.error(f"Failed to persist human decision to database: {e}")
            # Continue anyway - the workflow should not fail because of this
        
        # Clear human review data from Redis
        await redis_service.clear_human_review_data(request_id)
        
        # Log the decision
        logger.info(f"Human decision received for {request_id}: {decision.decision}")
        if decision.feedback:
            logger.info(f"Human feedback: {decision.feedback}")
        
        # Resume the workflow by continuing execution
        if decision.decision != "abort":
            # Resume the workflow with the human decision using the already updated state
            try:
                # Pass the already updated agent_state to avoid state synchronization issues
                final_state = await coordinator.resume_workflow_with_state(request_id, agent_state)
                logger.info(f"✅ Workflow resumed and completed for {request_id}")
            except Exception as e:
                logger.error(f"Failed to resume workflow for {request_id}: {e}")
                # Fallback: try the original method
                try:
                    logger.info(f"🔄 Attempting fallback resume for {request_id}")
                    final_state = await coordinator.resume_workflow(request_id)
                    logger.info(f"✅ Fallback resume successful for {request_id}")
                except Exception as e2:
                    logger.error(f"Fallback resume also failed for {request_id}: {e2}")
                    # Don't fail the endpoint - the decision is still recorded
        else:
            # Mark analysis as aborted
            agent_state.status = "aborted"
            await coordinator._save_intermediate_state(agent_state)
        
        return {
            "message": "Decision received successfully",
            "request_id": request_id,
            "decision": decision.decision,
            "status": "resumed" if decision.decision != "abort" else "aborted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing quality decision for {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process decision")


@router.get("/analysis/{request_id}/quality-issues")
async def get_quality_issues(
    request_id: str,
    coordinator: CompetitorAnalysisCoordinator = Depends(get_coordinator)
):
    """
    Get current quality issues for an analysis
    
    Returns all quality issues identified during the analysis,
    including their severity and suggested actions.
    """
    try:
        agent_state = await coordinator.get_agent_state(request_id)
        
        if not agent_state:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        quality_issues = [issue.dict() for issue in agent_state.retry_context.quality_feedback]
        
        return {
            "request_id": request_id,
            "quality_issues": quality_issues,
            "total_issues": len(quality_issues),
            "critical_issues": len(agent_state.get_critical_quality_issues()),
            "awaiting_review": agent_state.is_awaiting_human_review(),
            "retry_count": agent_state.retry_context.retry_count,
            "max_retries": agent_state.retry_context.max_retries
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quality issues for {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quality issues")


@router.get("/demo-mode/status")
async def get_demo_mode_status():
    """
    Get current demo mode status
    
    Returns whether the system is currently running in demo mode with mock data
    """
    try:
        demo_mode = os.getenv("TAVILY_DEMO_MODE", "False").lower() in ["true", "1", "yes"]
        return {
            "demo_mode": demo_mode,
            "description": "Demo mode uses mock data instead of real API calls" if demo_mode else "Using real API data"
        }
    except Exception as e:
        logger.error(f"Error getting demo mode status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get demo mode status")


@router.post("/demo-mode/toggle")
async def toggle_demo_mode():
    """
    Toggle demo mode on/off
    
    This switches between using real API data and mock data for searches.
    Note: This requires restarting services to take full effect.
    """
    try:
        current_demo_mode = os.getenv("TAVILY_DEMO_MODE", "False").lower() in ["true", "1", "yes"]
        new_demo_mode = not current_demo_mode
        
        # Update environment variable (note: this only affects current process)
        os.environ["TAVILY_DEMO_MODE"] = "True" if new_demo_mode else "False"
        
        logger.info(f"Demo mode toggled: {current_demo_mode} -> {new_demo_mode}")
        
        return {
            "message": "Demo mode toggled successfully",
            "previous_demo_mode": current_demo_mode,
            "current_demo_mode": new_demo_mode,
            "note": "Services should be restarted for full effect"
        }
    except Exception as e:
        logger.error(f"Error toggling demo mode: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle demo mode")


async def run_analysis_workflow(coordinator, analysis_request, request_id):
    """Run the analysis workflow asynchronously"""
    try:
        logger.info(f"Starting analysis workflow for request {request_id}")
        result = await coordinator.analyze_competitors_with_id(analysis_request, request_id)
        logger.info(f"Analysis workflow completed for request {request_id}")
    except Exception as e:
        logger.error(f"Analysis workflow failed: {e}")
        await coordinator.analysis_repository.update_analysis(
            request_id, 
            {
                "status": "failed", 
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }
        )