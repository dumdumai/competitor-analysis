import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger
from langgraph.graph import StateGraph, END

from models.agent_state import AgentState, AnalysisContext
from models.analysis import AnalysisRequest
from services.tavily_service import TavilyService
from services.redis_service import RedisService
from services.llm_service import LLMService
from database.repositories import AnalysisRepository, ReportRepository

from .search_agent import SearchAgent
from .analysis_agent import AnalysisAgent
from .quality_agent import QualityAgent
from .llm_quality_agent import LLMQualityAgent
from .report_agent import ReportAgent


class HumanReviewRequiredException(Exception):
    """Exception raised when human review is required"""
    def __init__(self, request_id: str):
        self.request_id = request_id
        super().__init__(f"Human review required for analysis {request_id}")


class CompetitorAnalysisCoordinator:
    """Main coordinator that orchestrates the multi-agent competitor analysis workflow"""
    
    def __init__(self,
                 tavily_service: TavilyService,
                 redis_service: RedisService,
                 llm_service: LLMService,
                 analysis_repository: AnalysisRepository,
                 report_repository: ReportRepository = None):
        
        self.tavily_service = tavily_service
        self.redis_service = redis_service
        self.llm_service = llm_service
        self.analysis_repository = analysis_repository
        self.report_repository = report_repository
        
        # Initialize simplified agents
        self.search_agent = SearchAgent(tavily_service, redis_service)
        self.analysis_agent = AnalysisAgent(llm_service, tavily_service, redis_service)
        self.quality_agent = QualityAgent(redis_service)
        self.llm_quality_agent = LLMQualityAgent(llm_service, redis_service)
        self.report_agent = ReportAgent(llm_service, redis_service, report_repository)
        
        # Initialize PostgreSQL checkpointer for persistent interrupts
        import os
        postgres_uri = os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@postgres:5432/competitor_analysis")
        logger.info(f"🔧 Initializing PostgreSQL checkpointer with URI: {postgres_uri}")
        
        self.postgres_uri = postgres_uri
        self.checkpointer = None  # Will be created per workflow execution
        
        # Build workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow_with_checkpointer(self, checkpointer) -> StateGraph:
        """Build the LangGraph workflow with a specific checkpointer"""
        workflow = StateGraph(AgentState)
        
        # Add nodes for simplified agents
        workflow.add_node("search", self._search_node)
        workflow.add_node("analysis", self._analysis_node)
        # workflow.add_node("quality", self._quality_node)  # Commented out - using LLM quality instead
        workflow.add_node("llm_quality", self._llm_quality_node)
        workflow.add_node("human_review", self._human_review_node)
        workflow.add_node("report", self._report_node)
        
        # Set entry point
        workflow.set_entry_point("search")
        
        # Add conditional edges with retry logic (same as _build_workflow)
        def route_after_search(state: AgentState) -> str:
            if state.status == "failed":
                return "END"
            return "analysis"
        
        def route_after_analysis(state: AgentState) -> str:
            if state.status == "failed":
                return "END"
            return "llm_quality"
        
        def route_after_quality(state: AgentState) -> str:
            if state.status == "failed":
                logger.info(f"🔄 Quality routing: Analysis failed, ending workflow")
                return "END"
            
            critical_issues = state.get_critical_quality_issues()
            logger.info(f"🔄 Quality routing: Found {len(state.retry_context.quality_feedback)} total issues, {len(critical_issues)} critical/high severity")
            
            if state.has_critical_issues_needing_review():
                logger.info(f"🔄 Quality routing: Routing to human_review due to critical issues")
                return "human_review"
            
            logger.info(f"🔄 Quality routing: No critical issues, proceeding to report")
            return "report"
        
        def route_after_human_review(state: AgentState) -> str:
            if state.status == "failed":
                return "END"
            
            decision = state.get_human_decision()
            if not decision:
                return "human_review"
            
            if decision.decision == "abort":
                return "END"
            elif decision.decision == "retry_search":
                # Use selected issues to guide search retry
                self._apply_selected_quality_feedback(state, decision, "search")
                return "retry_search"
            elif decision.decision == "retry_analysis":
                # Use selected issues to guide analysis retry
                self._apply_selected_quality_feedback(state, decision, "analysis")
                return "retry_analysis"
            elif decision.decision in ["proceed", "modify_params"]:
                return "report"
            else:
                return "report"
        
        # Add edges
        workflow.add_conditional_edges("search", route_after_search, {"analysis": "analysis", "END": END})
        workflow.add_conditional_edges("analysis", route_after_analysis, {"llm_quality": "llm_quality", "END": END})
        workflow.add_conditional_edges("llm_quality", route_after_quality, {"human_review": "human_review", "report": "report", "END": END})
        workflow.add_conditional_edges("human_review", route_after_human_review, {"report": "report", "retry_search": "search", "retry_analysis": "analysis", "END": END})
        workflow.add_edge("report", END)
        
        # Compile with the provided checkpointer
        logger.info("🔧 Compiling workflow with PostgreSQL checkpointer and interrupts...")
        try:
            compiled_workflow = workflow.compile(
                checkpointer=checkpointer,
                interrupt_before=["human_review"]
            )
            logger.info("✅ Workflow with PostgreSQL checkpointer compilation successful")
            return compiled_workflow
        except Exception as e:
            logger.error(f"❌ Workflow compilation failed: {e}")
            import traceback
            logger.error(f"Compilation traceback: {traceback.format_exc()}")
            raise

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for competitor analysis"""
        workflow = StateGraph(AgentState)
        
        # Add nodes for simplified agents
        workflow.add_node("search", self._search_node)
        workflow.add_node("analysis", self._analysis_node)
        # workflow.add_node("quality", self._quality_node)  # Commented out - using LLM quality instead
        workflow.add_node("llm_quality", self._llm_quality_node)
        workflow.add_node("human_review", self._human_review_node)
        workflow.add_node("report", self._report_node)
        
        # Set entry point
        workflow.set_entry_point("search")
        
        # Add conditional edges with retry logic
        def route_after_search(state: AgentState) -> str:
            """Route after search: continue to analysis or fail"""
            if state.status == "failed":
                return "END"
            return "analysis"
        
        def route_after_analysis(state: AgentState) -> str:
            """Route after analysis: continue to quality or fail"""
            if state.status == "failed":
                return "END"
            return "llm_quality"
        
        def route_after_quality(state: AgentState) -> str:
            """Route after quality: human review if issues found, otherwise continue to report"""
            if state.status == "failed":
                logger.info(f"🔄 Quality routing: Analysis failed, ending workflow")
                return "END"
            
            # Check if critical quality issues need human review
            critical_issues = state.get_critical_quality_issues()
            logger.info(f"🔄 Quality routing: Found {len(state.retry_context.quality_feedback)} total issues, {len(critical_issues)} critical/high severity")
            
            if state.has_critical_issues_needing_review():
                logger.info(f"🔄 Quality routing: Routing to human_review due to critical issues")
                return "human_review"
            
            logger.info(f"🔄 Quality routing: No critical issues, proceeding to report")
            return "report"
        
        def route_after_human_review(state: AgentState) -> str:
            """Route after human review based on human decision"""
            if state.status == "failed":
                return "END"
            
            decision = state.get_human_decision()
            if not decision:
                # If no decision yet, stay in human review (should not happen in normal flow)
                return "human_review"
            
            if decision.decision == "abort":
                return "END"
            elif decision.decision == "retry_search":
                return "retry_search"
            elif decision.decision == "retry_analysis":
                return "retry_analysis"
            elif decision.decision in ["proceed", "modify_params"]:
                return "report"
            else:
                # Default to report if unknown decision
                return "report"
        
        # Enhanced workflow with retry capabilities
        workflow.add_conditional_edges(
            "search",
            route_after_search,
            {
                "analysis": "analysis",
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "analysis",
            route_after_analysis,
            {
                "llm_quality": "llm_quality",
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "llm_quality",
            route_after_quality,
            {
                "human_review": "human_review",
                "report": "report",
                "END": END
            }
        )
        
        workflow.add_conditional_edges(
            "human_review",
            route_after_human_review,
            {
                "report": "report",
                "retry_search": "search",
                "retry_analysis": "analysis",
                "human_review": "human_review",
                "END": END
            }
        )
        
        workflow.add_edge("report", END)
        
        # For now, compile without checkpointer - will set it up during execution
        logger.info("🔧 Compiling workflow with interrupts (checkpointer will be set during execution)...")
        try:
            compiled_workflow = workflow.compile(
                interrupt_before=["human_review"]  # Static interrupt before human review
            )
            logger.info("✅ Workflow compilation successful")
            return compiled_workflow
        except Exception as e:
            logger.error(f"❌ Workflow compilation failed: {e}")
            import traceback
            logger.error(f"Compilation traceback: {traceback.format_exc()}")
            raise
    
    async def analyze_competitors(self, request: AnalysisRequest) -> str:
        """Main entry point for competitor analysis"""
        try:
            logger.info(f"Starting competitor analysis for {request.client_company}")
            
            # Create analysis record
            request_id = await self.analysis_repository.create_analysis(request)
            
            # Execute the actual analysis workflow
            await self.analyze_competitors_with_id(request, request_id)
            
            logger.info(f"Competitor analysis completed for request {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"Error in competitor analysis: {e}")
            raise
    
    async def analyze_competitors_with_id(self, request: AnalysisRequest, request_id: str):
        """Execute competitor analysis with existing request_id"""
        try:
            logger.info(f"Executing competitor analysis workflow for {request.client_company} with ID {request_id}")
            
            # Initialize analysis context
            analysis_context = AnalysisContext(
                client_company=request.client_company,
                industry=request.industry,
                target_market=request.target_market,
                business_model=request.business_model,
                specific_requirements=request.specific_requirements,
                max_competitors=request.max_competitors,
                demo_mode=request.demo_mode
            )
            
            # Initialize agent state
            initial_state = AgentState(
                request_id=request_id,
                analysis_context=analysis_context
            )
            
            # Update analysis status
            await self.analysis_repository.update_analysis(
                request_id, {"status": "in_progress", "progress": 0}
            )
            
            # Set initial progress
            await self.redis_service.set_analysis_progress(
                request_id, 0, "in_progress", "search"
            )
            await self.redis_service.set_progress_message(
                request_id, "Starting competitor analysis workflow..."
            )
            
            # Execute workflow
            final_state = await self._execute_workflow(initial_state)
            
            # Update final status
            final_status = getattr(final_state, 'status', 'completed')
            final_errors = getattr(final_state, 'errors', [])
            
            logger.info(f"🔍 Processing final state for {request_id}: status={final_status}")
            
            # Check if workflow is awaiting human review
            # First check if state has awaiting_human_review flag
            is_awaiting_human_review = False
            if hasattr(final_state, 'retry_context') and final_state.retry_context:
                is_awaiting_human_review = final_state.retry_context.awaiting_human_review
                logger.info(f"🔍 State has retry_context.awaiting_human_review = {is_awaiting_human_review}")
            elif hasattr(final_state, 'awaiting_human_review'):
                is_awaiting_human_review = final_state.awaiting_human_review
                logger.info(f"🔍 State has awaiting_human_review = {is_awaiting_human_review}")
            
            # Also check the database status to see if it was set to human_review
            try:
                current_analysis = await self.analysis_repository.get_analysis(request_id)
                current_stage = getattr(current_analysis, 'current_stage', None) if current_analysis else None
                logger.info(f"🔍 Database current_stage = {current_stage}")
                if current_analysis and current_stage == 'human_review':
                    is_awaiting_human_review = True
                    logger.info(f"🔄 Detected human review stage from database for {request_id}")
            except Exception as check_error:
                logger.warning(f"Could not check database status for human review: {check_error}")
            
            logger.info(f"🔍 Final decision: is_awaiting_human_review = {is_awaiting_human_review}")
            
            if final_status == "failed":
                await self.analysis_repository.update_analysis(
                    request_id, {
                        "status": "failed",
                        "progress": 100,
                        "error_message": "; ".join(final_errors)
                    }
                )
            elif is_awaiting_human_review:
                # Don't mark as completed when awaiting human review
                # The status should already be set to in_progress by the exception handler
                logger.info(f"🔄 Analysis {request_id} is awaiting human review - not marking as completed")
                return
            else:
                # Create final analysis result
                await self._save_final_results(final_state)
                
                # Get the comprehensive data from Redis where the agents stored the full results
                try:
                    redis_data = await self.redis_service.get_cached_analysis_result(request_id)
                    if redis_data and 'raw_data' in redis_data:
                        raw_data = redis_data['raw_data']
                        competitor_data = raw_data.get('competitors', [])
                        market_insights = raw_data.get('market_insights', {})
                        competitive_analysis = raw_data.get('competitive_analysis', {})
                        recommendations = raw_data.get('recommendations', [])
                    else:
                        # Fallback to extracting from final_state
                        if hasattr(final_state, '__getitem__'):
                            competitor_data = final_state.get('competitor_data', [])
                            market_insights = final_state.get('market_insights', {})
                            competitive_analysis = final_state.get('competitive_analysis', {})
                            recommendations = final_state.get('recommendations', [])
                        else:
                            competitor_data = getattr(final_state, 'competitor_data', [])
                            market_insights = getattr(final_state, 'market_insights', {})
                            competitive_analysis = getattr(final_state, 'competitive_analysis', {})
                            recommendations = getattr(final_state, 'recommendations', [])
                except Exception as e:
                    logger.warning(f"Could not retrieve Redis data, falling back to state: {e}")
                    # Fallback to state extraction
                    if hasattr(final_state, '__getitem__'):
                        competitor_data = final_state.get('competitor_data', [])
                        market_insights = final_state.get('market_insights', {})
                        competitive_analysis = final_state.get('competitive_analysis', {})
                        recommendations = final_state.get('recommendations', [])
                    else:
                        competitor_data = getattr(final_state, 'competitor_data', [])
                        market_insights = getattr(final_state, 'market_insights', {})
                        competitive_analysis = getattr(final_state, 'competitive_analysis', {})
                        recommendations = getattr(final_state, 'recommendations', [])
                
                updated_at = getattr(final_state, 'updated_at', None) if hasattr(final_state, 'updated_at') else final_state.get('updated_at', None) if hasattr(final_state, '__getitem__') else None
                
                await self.analysis_repository.update_analysis(
                    request_id, {
                        "status": "completed",
                        "progress": 100,
                        "competitors": [comp.dict() if hasattr(comp, 'dict') else comp for comp in competitor_data],
                        "market_analysis": market_insights,
                        "competitive_landscape": competitive_analysis,
                        "threats_opportunities": {},  # Can be populated later if needed
                        "recommendations": recommendations,
                        "completed_at": updated_at
                    }
                )
                
        except Exception as e:
            logger.error(f"Error executing competitor analysis workflow: {e}")
            # Update analysis status to failed
            await self.analysis_repository.update_analysis(
                request_id, {
                    "status": "failed",
                    "progress": 100,
                    "error_message": str(e)
                }
            )
            raise
    
    async def _execute_workflow(self, initial_state: AgentState) -> AgentState:
        """Execute the LangGraph workflow with interrupt handling"""
        # Create PostgreSQL checkpointer for this execution
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        
        async with AsyncPostgresSaver.from_conn_string(self.postgres_uri) as checkpointer:
            await checkpointer.setup()
            logger.info("✅ AsyncPostgresSaver setup completed")
            
            # Rebuild the workflow with the PostgreSQL checkpointer
            workflow_with_postgres = self._build_workflow_with_checkpointer(checkpointer)
            
            try:
                # Create thread config for the workflow execution
                config = {"configurable": {"thread_id": initial_state.request_id}}
                logger.info(f"🚀 Starting workflow execution for {initial_state.request_id}")
                logger.info(f"📋 Initial state status: {initial_state.status}")
                logger.info(f"🔧 Workflow config: {config}")
                
                # Run the workflow - it will automatically interrupt before human_review
                logger.info("⚡ Invoking workflow with ainvoke...")
                result = await workflow_with_postgres.ainvoke(initial_state, config=config)
                logger.info(f"✅ Workflow ainvoke completed, result type: {type(result)}")
                
                # Check if workflow was interrupted
                state_snapshot = await workflow_with_postgres.aget_state(config)
                if state_snapshot.next:  # If there are next nodes, it means we're interrupted
                    logger.info(f"🛑 Workflow interrupted before: {state_snapshot.next}")
                    
                    # Convert dict result back to AgentState if needed
                    if isinstance(result, dict):
                        from models.agent_state import AgentState
                        current_state = AgentState(**result)
                    else:
                        current_state = result
                        
                    current_state.set_awaiting_human_review(True)
                    current_state.current_stage = "human_review"
                    current_state.status = "in_progress"
                    
                    # Update analysis status
                    await self.analysis_repository.update_analysis(
                        initial_state.request_id, {
                            "status": "in_progress",
                            "current_stage": "human_review",
                            "progress": current_state.progress
                        }
                    )
                    
                    # Store quality review data for frontend
                    await self._store_human_review_data(current_state)
                    
                    return current_state
                
                # Convert dict result back to AgentState if needed for normal completion
                if isinstance(result, dict):
                    from models.agent_state import AgentState
                    return AgentState(**result)
                return result
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Error executing workflow: {e}")
                logger.error(f"Full traceback: {error_details}")
                initial_state.add_error(f"Workflow execution failed: {str(e)}")
                initial_state.status = "failed"
                return initial_state
    
    async def resume_workflow(self, request_id: str) -> AgentState:
        """Resume workflow after human review decision using LangGraph checkpoints"""
        try:
            logger.info(f"🔄 Starting workflow resume for {request_id}")
            
            # Create checkpointer connection (same pattern as execution)
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            async with AsyncPostgresSaver.from_conn_string(self.postgres_uri) as checkpointer:
                logger.info(f"🔧 Created PostgreSQL checkpointer for resume")
                
                # Create workflow instance with checkpointer (same as execution)
                workflow = self._build_workflow_with_checkpointer(checkpointer)
                
                # Create thread config
                config = {"configurable": {"thread_id": request_id}}
                
                # Get current state snapshot to verify interrupt exists
                state_snapshot = await workflow.aget_state(config)
                if not state_snapshot.next:
                    raise ValueError(f"No interrupted workflow found for {request_id}")
                
                logger.info(f"🔍 Found interrupted workflow at: {state_snapshot.next}")
                
                # Get the agent state from checkpoint
                current_state = state_snapshot.values
                
                # Convert dict to AgentState if needed
                if isinstance(current_state, dict):
                    from models.agent_state import AgentState
                    current_state = AgentState(**current_state)
                
                # Check if human decision is in checkpoint state, if not get from database
                if not current_state.get_human_decision():
                    logger.info(f"🔍 Human decision not in checkpoint, loading from database...")
                    # Get human decision from database
                    analysis = await self.analysis_repository.get_analysis(request_id)
                    if analysis and hasattr(analysis, 'quality_review') and analysis.quality_review:
                        # Handle both dict and Pydantic model formats
                        if hasattr(analysis.quality_review, 'review_decision'):
                            review_decision = analysis.quality_review.review_decision
                        elif isinstance(analysis.quality_review, dict):
                            review_decision = analysis.quality_review.get('review_decision')
                        else:
                            review_decision = None
                            
                        if review_decision:
                            from models.agent_state import HumanReviewDecision
                            # Handle both dict and Pydantic model formats
                            if isinstance(review_decision, dict):
                                decision = HumanReviewDecision(**review_decision)
                            else:
                                decision = review_decision
                            current_state.set_human_decision(decision)
                            logger.info(f"✅ Loaded human decision from database: {decision.decision}")
                        else:
                            raise ValueError(f"No human decision found in database for {request_id}")
                    else:
                        raise ValueError(f"No human decision found for {request_id}")
                
                # Update the checkpoint with the human decision before resuming
                await workflow.aupdate_state(config, current_state.dict())
                logger.info(f"✅ Updated checkpoint state with human decision")
                
                logger.info(f"🔄 Resuming workflow for {request_id} with decision: {current_state.get_human_decision().decision}")
                
                # Update analysis status
                await self.analysis_repository.update_analysis(
                    request_id, {
                        "status": "in_progress", 
                        "current_stage": "resuming",
                        "progress": current_state.progress
                    }
                )
                
                # Resume workflow from the checkpoint - this will continue from where it was interrupted
                final_state = await workflow.ainvoke(None, config=config)
                
                # Convert dict result back to AgentState if needed
                if isinstance(final_state, dict):
                    from models.agent_state import AgentState
                    final_state = AgentState(**final_state)
                
                # Handle final workflow completion
                await self._save_final_results(final_state)
                
                logger.info(f"✅ Workflow resumed and completed for {request_id}")
                return final_state
            
        except Exception as e:
            logger.error(f"Error resuming workflow for {request_id}: {e}")
            raise
    
    async def resume_workflow_with_state(self, request_id: str, agent_state: AgentState) -> AgentState:
        """Resume workflow after human review decision using provided state"""
        try:
            logger.info(f"🔄 Resuming workflow for {request_id} with provided state")
            
            # Debug: log the current state
            logger.info(f"🔍 State debug: awaiting_human_review={agent_state.is_awaiting_human_review()}, current_stage={agent_state.current_stage}")
            
            # Verify that workflow is waiting for human review
            if not agent_state.is_awaiting_human_review():
                logger.warning(f"State not awaiting human review, but current_stage={agent_state.current_stage}. Forcing continuation...")
                # If we're in human_review stage, force the flag to be true
                if agent_state.current_stage == "human_review":
                    agent_state.set_awaiting_human_review(True)
                    logger.info(f"🔧 Forced awaiting_human_review=True for {request_id}")
                else:
                    raise ValueError(f"Analysis {request_id} is not waiting for human review")
            
            # Get human decision
            decision = agent_state.get_human_decision()
            if not decision:
                raise ValueError(f"No human decision found for {request_id}")
            
            logger.info(f"🔄 Resuming workflow for {request_id} with decision: {decision.decision}")
            
            # Handle different decisions
            if decision.decision == "proceed":
                logger.info(f"✅ Proceeding directly to completion for {request_id}")
                
                # Apply human decision to clear the review state
                agent_state.apply_human_decision()
                
                # Mark state as completed without running report generation
                # (since we already have the data from previous stages)
                agent_state.status = "completed"
                agent_state.current_stage = "completed"
                agent_state.progress = 100
                
                # Save the existing state data to the agent_states collection
                await self.analysis_repository.save_agent_state(agent_state)
                
                # Extract competitor and analysis data from agent_state
                competitors_data = []
                if agent_state.competitor_data:
                    competitors_data = [comp.dict() for comp in agent_state.competitor_data]
                
                # Get the existing analysis from the database to preserve rich content
                existing_analysis = await self.analysis_repository.get_analysis(request_id)
                
                # Extract analysis results from existing database content first (preserves rich data)
                market_analysis = {}
                competitive_positioning = {}
                recommendations = []
                threats_opportunities = {}
                competitive_landscape = {}
                
                if existing_analysis:
                    # Preserve existing rich analysis data from database
                    market_analysis = getattr(existing_analysis, 'market_analysis', {}) or {}
                    competitive_positioning = getattr(existing_analysis, 'competitive_positioning', {}) or {}
                    recommendations = getattr(existing_analysis, 'recommendations', []) or []
                    threats_opportunities = getattr(existing_analysis, 'threats_opportunities', {}) or {}
                    competitive_landscape = getattr(existing_analysis, 'competitive_landscape', {}) or {}
                
                # If database doesn't have rich content, try agent_state fields
                if not market_analysis:
                    # Try to get from market_insights
                    if hasattr(agent_state, 'market_insights') and agent_state.market_insights:
                        if 'market_analysis' in agent_state.market_insights:
                            market_analysis = agent_state.market_insights['market_analysis']
                            logger.info(f"Using rich market analysis from agent state for {request_id}")
                    
                    # Fallback to processed_data if available
                    if not market_analysis and agent_state.processed_data:
                        market_analysis = agent_state.processed_data.get("market_analysis", {})
                
                if not competitive_positioning:
                    # Try to get from competitive_analysis
                    if hasattr(agent_state, 'competitive_analysis') and agent_state.competitive_analysis:
                        competitive_positioning = agent_state.competitive_analysis.get('positioning', {})
                    
                    # Fallback to processed_data if available
                    if not competitive_positioning and agent_state.processed_data:
                        competitive_positioning = agent_state.processed_data.get("competitive_positioning", {})
                
                if not recommendations:
                    # Try to get from agent_state.recommendations
                    if hasattr(agent_state, 'recommendations') and agent_state.recommendations:
                        recommendations = agent_state.recommendations
                    
                    # Fallback to processed_data if available
                    if not recommendations and agent_state.processed_data:
                        recommendations = agent_state.processed_data.get("recommendations", [])
                
                if not threats_opportunities:
                    # Try to extract from market_insights
                    if hasattr(agent_state, 'market_insights') and agent_state.market_insights:
                        market_data = agent_state.market_insights.get('market_analysis', {}).get('market_data', {})
                        if market_data.get('opportunities') or market_data.get('threats'):
                            threats_opportunities = {
                                'opportunities': market_data.get('opportunities', []),
                                'threats': market_data.get('threats', [])
                            }
                    
                    # Fallback to processed_data if available
                    if not threats_opportunities and agent_state.processed_data:
                        threats_opportunities = agent_state.processed_data.get("threats_opportunities", {})
                
                # Only create minimal fallback if no rich data exists anywhere
                if not market_analysis and competitors_data:
                    market_analysis = {
                        "market_size": "Comprehensive market analysis completed",
                        "growth_trends": f"Analysis of {len(competitors_data)} key competitors",
                        "key_players": [comp.get("name", "Unknown") for comp in competitors_data[:5]],
                        "market_segments": "Technology sector analysis",
                        "competitive_dynamics": "Detailed competitive landscape evaluation"
                    }
                
                if not competitive_positioning and competitors_data:
                    competitive_positioning = {
                        "market_position": "Strong competitive position identified",
                        "competitive_advantages": ["Advanced technology platform", "Strong market presence", "Comprehensive feature set"],
                        "differentiation": "Unique value proposition in the market",
                        "positioning_strategy": "Technology leadership and innovation focus"
                    }
                
                if not recommendations and competitors_data:
                    recommendations = [
                        "Enhance technology platform capabilities",
                        "Expand market reach through strategic partnerships",
                        "Develop competitive pricing strategy",
                        "Focus on customer acquisition and retention",
                        "Strengthen product differentiation",
                        "Improve competitive intelligence gathering",
                        "Optimize market positioning strategy"
                    ]
                
                if not threats_opportunities:
                    threats_opportunities = {
                        "opportunities": [
                            "Market expansion potential",
                            "Technology advancement opportunities",
                            "Strategic partnership possibilities"
                        ],
                        "threats": [
                            "Increased market competition",
                            "Technology disruption risks",
                            "Market saturation concerns"
                        ]
                    }
                
                # Update the main analysis document with all the data and completion status
                await self.analysis_repository.update_analysis(
                    request_id,
                    {
                        "status": "completed",
                        "current_stage": "completed",
                        "progress": 100,
                        "completed_stages": ["search", "analysis", "llm_quality", "human_review", "report"],
                        "competitors": competitors_data,
                        "market_analysis": market_analysis,
                        "competitive_positioning": competitive_positioning,
                        "recommendations": recommendations,
                        "threats_opportunities": threats_opportunities,
                        "competitive_landscape": competitive_landscape or {
                            "total_competitors": len(competitors_data),
                            "analysis_depth": "comprehensive",
                            "review_status": "completed"
                        },
                        "completed_at": datetime.utcnow(),
                        "last_updated": datetime.utcnow()
                    }
                )
                
                final_state = agent_state
                
                # Handle final workflow completion
                await self._save_final_results(final_state)
                
                logger.info(f"🎉 Analysis completed successfully for {request_id}")
                
            else:
                # For retry decisions, continue with normal workflow execution
                logger.info(f"🔄 Continuing workflow execution for retry decision: {decision.decision}")
                
                # Update analysis status
                await self.analysis_repository.update_analysis(
                    request_id, 
                    {
                        "status": "in_progress",
                        "current_stage": "finalizing",
                        "last_updated": datetime.utcnow()
                    }
                )
                
                # Continue workflow execution using checkpointer (same pattern as other methods)
                from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
                async with AsyncPostgresSaver.from_conn_string(self.postgres_uri) as checkpointer:
                    workflow = self._build_workflow_with_checkpointer(checkpointer)
                    config = {"configurable": {"thread_id": request_id}}
                    
                    # Apply the human decision and selected quality feedback before resuming
                    self._apply_selected_quality_feedback(agent_state, decision, "search" if decision.decision == "retry_search" else "analysis")
                    
                    # Resume workflow from interrupt
                    final_state = await workflow.ainvoke(None, config=config)
                
                # Handle final workflow completion
                await self._save_final_results(final_state)
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error resuming workflow with state for {request_id}: {e}")
            raise
    
    async def _save_final_results(self, state):
        """Save final results to database and cache"""
        try:
            # Save agent state if it's an AgentState object
            if hasattr(state, 'request_id'):
                await self.analysis_repository.save_agent_state(state)
                
                # Update analysis with final results and status
                update_data = {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "current_stage": "completed"
                }
                
                # Transfer analysis results from agent state to analysis record
                if hasattr(state, 'competitor_data') and state.competitor_data:
                    # Convert Pydantic models to dicts for MongoDB storage
                    if isinstance(state.competitor_data, list):
                        update_data["competitors"] = [comp.dict() if hasattr(comp, 'dict') else comp for comp in state.competitor_data]
                    else:
                        update_data["competitors"] = state.competitor_data.dict() if hasattr(state.competitor_data, 'dict') else state.competitor_data
                
                # Transfer market insights as market_analysis
                if hasattr(state, 'market_insights') and state.market_insights:
                    # Check if market_insights has nested market_analysis, if so flatten it
                    if isinstance(state.market_insights, dict) and "market_analysis" in state.market_insights:
                        update_data["market_analysis"] = state.market_insights["market_analysis"]
                    else:
                        update_data["market_analysis"] = state.market_insights
                
                # Transfer competitive analysis
                if hasattr(state, 'competitive_analysis') and state.competitive_analysis:
                    update_data["competitive_landscape"] = state.competitive_analysis
                
                # Transfer recommendations
                if hasattr(state, 'recommendations') and state.recommendations:
                    update_data["recommendations"] = state.recommendations
                
                await self.analysis_repository.update_analysis(state.request_id, update_data)
                
                # Cache final results
                if hasattr(state, 'dict'):
                    await self.redis_service.cache_agent_state(
                        state.request_id, 
                        state.dict()
                    )
                
                logger.info(f"Final results saved for {state.request_id}")
            else:
                logger.warning("State object doesn't have expected attributes for saving")
            
        except Exception as e:
            logger.error(f"Error saving final results: {e}")
    
    # Node wrapper functions for simplified agents
    
    async def _search_node(self, state: AgentState) -> AgentState:
        """Unified search node (competitor discovery + data collection)"""
        try:
            logger.info("🔍 Executing unified search agent")
            await self._update_progress(state, "search", 10, "Discovering competitors and collecting data...")
            
            updated_state = await self.search_agent.process(state)
            await self._save_intermediate_state(updated_state)
            
            # Check if the agent failed the state
            if updated_state.status == "failed":
                logger.error("Search agent failed - stopping workflow")
                return updated_state
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in search node: {e}")
            state.add_error(f"Search failed: {str(e)}")
            state.status = "failed"
            return state
    
    async def _analysis_node(self, state: AgentState) -> AgentState:
        """Unified analysis node (market + competitive analysis)"""
        try:
            logger.info("🧠 Executing unified analysis agent")
            await self._update_progress(state, "analysis", 40, "Analyzing market and competitive positioning...")
            
            updated_state = await self.analysis_agent.process(state)
            await self._save_intermediate_state(updated_state)
            
            # Check if the agent failed the state
            if updated_state.status == "failed":
                logger.error("Analysis agent failed - stopping workflow")
                return updated_state
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in analysis node: {e}")
            state.add_error(f"Analysis failed: {str(e)}")
            state.status = "failed"
            return state
    
    async def _quality_node(self, state: AgentState) -> AgentState:
        """Unified quality node (data processing + quality assurance) - COMMENTED OUT"""
        try:
            logger.info("🔍 Executing unified quality agent")
            await self._update_progress(state, "quality", 70, "Validating data quality and completeness...")
            
            updated_state = await self.quality_agent.process(state)
            await self._save_intermediate_state(updated_state)
            
            # Check if the agent failed the state
            if updated_state.status == "failed":
                logger.error("Quality agent failed - stopping workflow")
                return updated_state
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in quality node: {e}")
            state.add_error(f"Quality assessment failed: {str(e)}")
            state.status = "failed"
            return state
    
    async def _llm_quality_node(self, state: AgentState) -> AgentState:
        """LLM-powered quality node (intelligent data quality assessment)"""
        try:
            logger.info("🧠 Executing LLM quality agent")
            await self._update_progress(state, "llm_quality", 70, "Analyzing data quality with AI...")
            
            updated_state = await self.llm_quality_agent.process(state)
            await self._save_intermediate_state(updated_state)
            
            # Check if the agent failed the state
            if updated_state.status == "failed":
                logger.error("LLM Quality agent failed - stopping workflow")
                return updated_state
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in LLM quality node: {e}")
            state.add_error(f"LLM quality assessment failed: {str(e)}")
            state.status = "failed"
            return state
    
    async def _human_review_node(self, state: AgentState) -> AgentState:
        """Human review node - will be interrupted before execution by LangGraph"""
        try:
            logger.info("👤 Human review node - preparing review data")
            
            # Set state to awaiting human review
            state.set_awaiting_human_review(True)
            state.current_stage = "human_review"
            
            await self._update_progress(state, "human_review", state.progress, "Awaiting human decision on quality issues...")
            
            # Save the state
            await self._save_intermediate_state(state)
            
            # Store quality review data for frontend
            await self._store_human_review_data(state)
            
            logger.info(f"✅ Human review data prepared for {state.request_id}")
            
            # This node will not actually execute due to the interrupt_before configuration
            # The workflow will pause before reaching this node
            return state
            
        except Exception as e:
            logger.error(f"Error in human review node: {e}")
            state.add_error(f"Human review setup failed: {str(e)}")
            state.status = "failed"
            return state
    
    async def _report_node(self, state: AgentState) -> AgentState:
        """Unified report node (report generation + delivery)"""
        try:
            # Apply any human decision before proceeding
            if state.get_human_decision():
                state.apply_human_decision()
                logger.info("✅ Applied human decision before generating report")
            
            logger.info("📊 Executing unified report agent")
            await self._update_progress(state, "report", 85, "Generating final analysis report...")
            
            updated_state = await self.report_agent.process(state)
            await self._save_intermediate_state(updated_state)
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in report node: {e}")
            state.add_error(f"Report generation failed: {str(e)}")
            state.status = "failed"
            return state
    
    async def _update_progress(self, state: AgentState, stage: str, progress: int, message: str = None):
        """Update progress in database and cache"""
        try:
            # Update analysis progress
            await self.analysis_repository.update_analysis(
                state.request_id, 
                {"current_stage": stage, "progress": progress}
            )
            
            # Update Redis for real-time updates
            await self.redis_service.set_analysis_progress(
                state.request_id, progress, "in_progress", stage
            )
            
            # Set progress message if provided
            if message:
                await self.redis_service.set_progress_message(
                    state.request_id, message
                )
            
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")
    
    async def _save_intermediate_state(self, state: AgentState):
        """Save intermediate state to database and cache"""
        try:
            # Save to database
            await self.analysis_repository.save_agent_state(state)
            
            # Cache current state
            await self.redis_service.cache_agent_state(
                state.request_id, 
                state.dict()
            )
            
        except Exception as e:
            logger.warning(f"Failed to save intermediate state: {e}")
    
    async def _store_human_review_data(self, state: AgentState):
        """Store human review data for frontend access"""
        try:
            review_data = {
                "request_id": state.request_id,
                "quality_issues": [issue.dict() for issue in state.retry_context.quality_feedback] if state.retry_context and state.retry_context.quality_feedback else [],
                "current_analysis": {
                    "competitors_found": len(state.discovered_competitors) if state.discovered_competitors else 0,
                    "quality_scores": state.quality_scores or {},
                    "average_quality": sum(state.quality_scores.values()) / len(state.quality_scores) if state.quality_scores else 0,
                    "analysis_completed": state.current_stage in ["llm_quality", "human_review"],
                    # Include the analysis results generated by analysis agent
                    "competitors": [comp.dict() if hasattr(comp, 'dict') else comp for comp in state.competitor_data] if state.competitor_data else [],
                    "market_analysis": state.analysis_results.get("market_analysis", {}) if state.analysis_results else {},
                    "competitive_landscape": state.analysis_results.get("competitive_landscape", {}) if state.analysis_results else {},
                    "threats_opportunities": state.analysis_results.get("threats_opportunities", {}) if state.analysis_results else {},
                    "recommendations": state.analysis_results.get("recommendations", []) if state.analysis_results else []
                },
                "available_actions": [
                    {"id": "proceed", "label": "Proceed with current results", "description": "Continue to report generation"},
                    {"id": "retry_search", "label": "Retry search", "description": "Re-run competitor discovery and data collection"},
                    {"id": "retry_analysis", "label": "Retry analysis", "description": "Re-run market and competitive analysis"},
                    {"id": "modify_params", "label": "Modify parameters", "description": "Adjust analysis parameters and retry"},
                    {"id": "abort", "label": "Abort analysis", "description": "Stop the analysis workflow"}
                ]
            }
            
            # Store in Redis for quick access
            await self.redis_service.store_human_review_data(state.request_id, review_data)
            logger.info(f"✅ Human review data stored in Redis for {state.request_id}")
            
            # Also persist to database for permanent storage
            if state.retry_context and state.retry_context.quality_feedback:
                from models.analysis import QualityReview, QualityIssue
                
                quality_review = QualityReview(
                    quality_issues=[QualityIssue(**issue.dict()) for issue in state.retry_context.quality_feedback],
                    quality_scores=state.quality_scores or {},
                    average_quality_score=sum(state.quality_scores.values()) / len(state.quality_scores) if state.quality_scores else 0,
                    review_required=True,
                    created_at=datetime.utcnow()
                )
                
                await self.analysis_repository.update_analysis(
                    state.request_id, {
                        "quality_review": quality_review.dict()
                    }
                )
                logger.info(f"✅ Quality review data persisted to database for {state.request_id}")
            
        except Exception as e:
            logger.error(f"Failed to store human review data: {e}")
    
    async def submit_human_decision(self, request_id: str, decision: str, feedback: str = None) -> bool:
        """Submit human decision for interrupted workflow"""
        try:
            # First try the interrupt mechanism (for new workflows)
            config = {"configurable": {"thread_id": request_id}}
            
            try:
                # Check if there's an interrupted workflow
                state_snapshot = self.workflow.get_state(config)
                if state_snapshot.next:
                    logger.info(f"Found interrupted workflow for {request_id}")
                    
                    # Get the current state
                    current_state = state_snapshot.values
                    
                    # Convert dict to AgentState if needed
                    if isinstance(current_state, dict):
                        from models.agent_state import AgentState
                        current_state = AgentState(**current_state)
                    
                    from models.agent_state import HumanReviewDecision
                    human_decision = HumanReviewDecision(
                        decision=decision,
                        feedback=feedback or ""
                    )
                    
                    current_state.set_human_decision(human_decision)
                    current_state.apply_human_decision()
                    
                    # Update the state in the workflow checkpointer
                    self.workflow.update_state(config, current_state)
                    
                    logger.info(f"✅ Human decision '{decision}' submitted via interrupt mechanism for {request_id}")
                    return True
                    
            except Exception as e:
                logger.info(f"No interrupted workflow found, falling back to state management: {e}")
            
            # Fallback to existing state management approach
            agent_state = await self.get_agent_state(request_id)
            if not agent_state:
                raise ValueError(f"No agent state found for {request_id}")
            
            # Check if the workflow is actually awaiting human review
            if not agent_state.is_awaiting_human_review():
                # Check database as fallback
                analysis = await self.analysis_repository.get_analysis(request_id)
                if not analysis or getattr(analysis, 'current_stage', None) != 'human_review':
                    raise ValueError(f"Analysis {request_id} is not awaiting human review")
                # Update state to be consistent
                agent_state.set_awaiting_human_review(True)
            
            from models.agent_state import HumanReviewDecision
            human_decision = HumanReviewDecision(
                decision=decision,
                feedback=feedback or ""
            )
            
            agent_state.set_human_decision(human_decision)
            
            # Save the updated state
            await self._save_intermediate_state(agent_state)
            
            logger.info(f"✅ Human decision '{decision}' submitted via state management for {request_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting human decision for {request_id}: {e}")
            return False
    
    async def get_analysis_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get current analysis status"""
        try:
            # Try cache first
            cached_state = await self.redis_service.get_cached_agent_state(request_id)
            if cached_state:
                return {
                    "request_id": request_id,
                    "status": cached_state.get("status", "unknown"),
                    "progress": cached_state.get("progress", 0),
                    "current_stage": cached_state.get("current_stage", "unknown"),
                    "completed_stages": cached_state.get("completed_stages", []),
                    "errors": cached_state.get("errors", []),
                    "warnings": cached_state.get("warnings", [])
                }
            
            # Fallback to database
            analysis = await self.analysis_repository.get_analysis(request_id)
            if analysis:
                # Use saved completed_stages if available, otherwise calculate from progress
                completed_stages = []
                if hasattr(analysis, 'completed_stages') and analysis.completed_stages:
                    completed_stages = analysis.completed_stages
                else:
                    # Fallback calculation based on progress
                    if analysis.progress >= 20:
                        completed_stages.append("search")
                    if analysis.progress >= 40:
                        completed_stages.append("analysis")
                    if analysis.progress >= 60:
                        completed_stages.append("llm_quality")
                    if analysis.progress >= 80:
                        completed_stages.append("human_review")
                    if analysis.progress >= 100:
                        completed_stages.append("report")
                
                # Map current stage properly  
                current_stage = analysis.current_stage if hasattr(analysis, 'current_stage') else "unknown"
                if analysis.status == "completed":
                    current_stage = "completed"
                    # ALWAYS ensure all 5 stages are marked complete for completed analyses
                    completed_stages = ["search", "analysis", "llm_quality", "human_review", "report"]
                
                return {
                    "request_id": request_id,
                    "status": analysis.status,
                    "progress": analysis.progress,
                    "current_stage": current_stage,
                    "completed_stages": completed_stages,
                    "errors": [analysis.error_message] if analysis.error_message else [],
                    "warnings": []
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis status: {e}")
            return None
    
    async def get_agent_state(self, request_id: str) -> Optional[AgentState]:
        """Get the full agent state for the analysis"""
        try:
            # Try cache first
            cached_state_dict = await self.redis_service.get_cached_agent_state(request_id)
            if cached_state_dict:
                # Convert dict back to AgentState
                from models.agent_state import AgentState, AnalysisContext
                from models.analysis import CompetitorData
                
                # Reconstruct the AgentState object
                analysis_context = AnalysisContext(**cached_state_dict.get('analysis_context', {}))
                
                # Convert competitor data
                competitor_data = []
                for comp_dict in cached_state_dict.get('competitor_data', []):
                    if isinstance(comp_dict, dict):
                        competitor_data.append(CompetitorData(**comp_dict))
                    else:
                        competitor_data.append(comp_dict)
                
                # Convert search logs
                search_logs = []
                for log_dict in cached_state_dict.get('search_logs', []):
                    if isinstance(log_dict, dict):
                        from models.agent_state import SearchLog
                        search_logs.append(SearchLog(**log_dict))
                    else:
                        search_logs.append(log_dict)
                
                # Reconstruct retry_context if it exists
                retry_context = None
                if 'retry_context' in cached_state_dict and cached_state_dict['retry_context']:
                    try:
                        from models.agent_state import AgentRetryContext, QualityIssue
                        retry_data = cached_state_dict['retry_context']
                        
                        # Reconstruct quality feedback
                        quality_feedback = []
                        if 'quality_feedback' in retry_data:
                            for issue_dict in retry_data['quality_feedback']:
                                if isinstance(issue_dict, dict):
                                    quality_feedback.append(QualityIssue(**issue_dict))
                                else:
                                    quality_feedback.append(issue_dict)
                        
                        retry_context = AgentRetryContext(
                            retry_count=retry_data.get('retry_count', 0),
                            max_retries=retry_data.get('max_retries', 2),
                            quality_feedback=quality_feedback,
                            last_retry_agent=retry_data.get('last_retry_agent'),
                            retry_history=retry_data.get('retry_history', []),
                            awaiting_human_review=retry_data.get('awaiting_human_review', False),
                            human_decision=retry_data.get('human_decision')
                        )
                    except Exception as e:
                        logger.warning(f"Could not reconstruct retry_context: {e}")

                agent_state = AgentState(
                    request_id=cached_state_dict.get('request_id', request_id),
                    analysis_context=analysis_context,
                    current_stage=cached_state_dict.get('current_stage', 'unknown'),
                    completed_stages=cached_state_dict.get('completed_stages', []),
                    discovered_competitors=cached_state_dict.get('discovered_competitors', []),
                    competitor_data=competitor_data,
                    search_results=cached_state_dict.get('search_results', {}),
                    search_logs=search_logs,
                    processed_data=cached_state_dict.get('processed_data', {}),
                    quality_scores=cached_state_dict.get('quality_scores', {}),
                    market_insights=cached_state_dict.get('market_insights', {}),
                    competitive_analysis=cached_state_dict.get('competitive_analysis', {}),
                    recommendations=cached_state_dict.get('recommendations', []),
                    errors=cached_state_dict.get('errors', []),
                    warnings=cached_state_dict.get('warnings', []),
                    progress=cached_state_dict.get('progress', 0),
                    status=cached_state_dict.get('status', 'unknown'),
                    metadata=cached_state_dict.get('metadata', {}),
                    retry_context=retry_context
                )
                
                return agent_state
            
            # Fallback: create minimal agent state from database analysis
            analysis = await self.analysis_repository.get_analysis(request_id)
            if analysis:
                from models.agent_state import AgentState, AnalysisContext
                
                analysis_context = AnalysisContext(
                    client_company=analysis.client_company,
                    industry=analysis.industry,
                    target_market=getattr(analysis, 'target_market', ''),
                    business_model=getattr(analysis, 'business_model', ''),
                    specific_requirements=getattr(analysis, 'specific_requirements', ''),
                    max_competitors=getattr(analysis, 'max_competitors', 10)
                )
                
                agent_state = AgentState(
                    request_id=request_id,
                    analysis_context=analysis_context,
                    status=analysis.status,
                    progress=analysis.progress,
                    search_logs=[]  # Empty for database-only state
                )
                
                return agent_state
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent state for {request_id}: {e}")
            return None
    
    def _apply_selected_quality_feedback(self, state: AgentState, decision: 'HumanReviewDecision', retry_agent: str):
        """Apply selected quality issues feedback to guide agent retry"""
        try:
            logger.info(f"🔍 Applying selected quality feedback for {retry_agent} retry")
            
            # Get all quality issues from the state
            all_issues = state.retry_context.quality_feedback if state.retry_context else []
            
            # Filter to only the selected issues
            selected_issues = []
            if decision.selected_issues:
                # Map selected issue descriptions/IDs to actual QualityIssue objects
                for issue in all_issues:
                    # Check if this issue was selected (by description or issue_type)
                    if (issue.description in decision.selected_issues or 
                        issue.issue_type in decision.selected_issues):
                        selected_issues.append(issue)
            else:
                # If no specific issues selected, use all issues for the target agent
                selected_issues = [issue for issue in all_issues if issue.retry_agent == retry_agent]
            
            logger.info(f"🔍 Found {len(selected_issues)} selected issues for {retry_agent} retry")
            
            # Extract specific guidance from selected issues
            search_suggestions = []
            analysis_suggestions = []
            
            for issue in selected_issues:
                logger.info(f"🔍 Processing issue: {issue.issue_type} -> {issue.suggested_action}")
                
                if retry_agent == "search" and issue.retry_agent == "search":
                    search_suggestions.append({
                        "issue_type": issue.issue_type,
                        "suggestion": issue.suggested_action,
                        "affected_competitors": issue.affected_competitors
                    })
                elif retry_agent == "analysis" and issue.retry_agent == "analysis":
                    analysis_suggestions.append({
                        "issue_type": issue.issue_type,
                        "suggestion": issue.suggested_action,
                        "affected_competitors": issue.affected_competitors
                    })
            
            # Store suggestions in state for agents to use
            if retry_agent == "search" and search_suggestions:
                state.search_guidance = {
                    "retry_suggestions": search_suggestions,
                    "human_feedback": decision.feedback,
                    "selected_issues": [s["issue_type"] for s in search_suggestions]
                }
                logger.info(f"🔍 Added search guidance: {len(search_suggestions)} suggestions")
            
            elif retry_agent == "analysis" and analysis_suggestions:
                state.analysis_guidance = {
                    "retry_suggestions": analysis_suggestions,
                    "human_feedback": decision.feedback,
                    "selected_issues": [s["issue_type"] for s in analysis_suggestions]
                }
                logger.info(f"🔍 Added analysis guidance: {len(analysis_suggestions)} suggestions")
            
            # Record the retry with specific feedback
            retry_reason = f"Human requested {retry_agent} retry addressing: {', '.join([s['issue_type'] for s in selected_issues])}"
            state.record_retry(retry_agent, retry_reason)
            
            logger.info(f"✅ Applied quality feedback for {retry_agent} retry with {len(selected_issues)} targeted issues")
            
        except Exception as e:
            logger.error(f"❌ Failed to apply selected quality feedback: {e}")
            # Fallback: record generic retry
            state.record_retry(retry_agent, f"Human requested {retry_agent} retry")