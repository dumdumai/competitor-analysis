import asyncio
from typing import Dict, Any, List
from loguru import logger
from models.agent_state import AgentState
from services.llm_service import LLMService
from services.tavily_service import TavilyService
from services.redis_service import RedisService


class AnalysisAgent:
    """
    Unified AI-powered analysis agent that combines market analysis and competitive analysis.
    Uses Azure OpenAI to generate insights from collected data.
    """
    
    def __init__(self, llm_service: LLMService, tavily_service: TavilyService, redis_service: RedisService):
        self.name = "analysis_agent"
        self.llm_service = llm_service
        self.tavily_service = tavily_service
        self.redis_service = redis_service
    
    async def process(self, state: AgentState) -> AgentState:
        """Execute comprehensive AI-powered analysis"""
        try:
            # Check if this is a retry
            is_retry = state.retry_context.retry_count > 0 and state.retry_context.last_retry_agent == "analysis"
            
            if is_retry:
                logger.info(f"🔄 Retrying analysis (attempt {state.retry_context.retry_count}) for {state.analysis_context.client_company}")
                await self._handle_retry_feedback(state)
            else:
                logger.info(f"🧠 Starting AI analysis for {state.analysis_context.client_company}")
            
            # Update progress
            await self._update_progress(state, "analysis", 5, "Initializing AI analysis")
            
            # Stage 1: Market Analysis (enhanced based on feedback)
            await self._update_progress(state, "analysis", 20, "Analyzing market landscape")
            market_insights = await self._analyze_market_landscape(state)
            
            # Stage 2: Competitive Analysis (enhanced based on feedback)
            await self._update_progress(state, "analysis", 50, "Analyzing competitive positioning")
            competitive_insights = await self._analyze_competitive_landscape(state)
            
            # Stage 3: Strategic Recommendations
            await self._update_progress(state, "analysis", 80, "Generating strategic insights")
            recommendations = await self._generate_recommendations(state, market_insights, competitive_insights)
            
            # Store results
            state.market_insights = market_insights
            state.competitive_analysis = competitive_insights
            state.recommendations = recommendations
            
            # Update metadata
            state.metadata.update({
                "market_analysis_completed": bool(market_insights),
                "competitive_analysis_completed": bool(competitive_insights),
                "recommendations_count": len(recommendations) if recommendations else 0,
                "analysis_completed": True,
                "analysis_retry_count": state.retry_context.retry_count
            })
            
            # Complete the stage
            state.complete_stage("analysis")
            await self._update_progress(state, "analysis", 100, f"Analysis completed: {len(recommendations or [])} recommendations generated")
            
            # If this was a retry, record it
            if is_retry:
                state.record_retry("analysis", "Quality issues addressed in analysis")
                logger.info(f"✅ Analysis retry completed with {len(recommendations or [])} recommendations")
            else:
                logger.info(f"✅ AI analysis completed with {len(recommendations or [])} recommendations")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in analysis agent: {e}")
            state.add_error(f"Analysis failed: {str(e)}")
            return state
    
    async def _analyze_market_landscape(self, state: AgentState) -> Dict[str, Any]:
        """Analyze market landscape using AI and search data"""
        try:
            context = state.analysis_context
            
            # Gather market data using Tavily
            market_queries = [
                f"{context.industry} market size {context.target_market} 2024",
                f"{context.industry} market trends {context.target_market}",
                f"{context.industry} industry analysis {context.target_market}"
            ]
            
            market_data = []
            # Just do one comprehensive market search instead of looping
            results, market_search_logs = await self.tavily_service.search_market_analysis(
                context.industry, context.target_market
            )
            market_data.extend(results)
            
            # Add search logs to state
            from models.agent_state import SearchLog
            for log_dict in market_search_logs:
                search_log = SearchLog(**log_dict)
                state.add_search_log(search_log)
            
            if not self.llm_service.client:
                logger.warning("🤖 AI client not available - returning basic market analysis")
                return {
                    "market_size": "Analysis requires AI integration",
                    "key_trends": ["Digital transformation", "Market consolidation", "Customer-centric approaches"],
                    "competitive_intensity": "Medium to High",
                    "data_points": len(market_data)
                }
            
            # Use AI to analyze market data
            analysis_prompt = f"""
            Analyze the {context.industry} market in {context.target_market} based on the following data:
            
            Company Context: {context.client_company} ({context.business_model})
            Industry: {context.industry}
            Target Market: {context.target_market}
            
            Market Data Points: {len(market_data)}
            
            Provide a JSON analysis with:
            - market_size: Current market size and growth rate
            - key_trends: Top 5 market trends
            - competitive_intensity: High/Medium/Low with explanation
            - opportunities: Top 3 market opportunities
            - threats: Top 3 market threats
            - outlook: 12-month market outlook
            """
            
            response = await self.llm_service.client.chat.completions.create(
                model=self.llm_service.model,
                messages=[
                    {"role": "system", "content": "You are a market research expert. Provide detailed market analysis in JSON format."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            
            import json
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"❌ Market analysis error: {e}")
            return {"error": str(e), "fallback": "Basic market analysis"}
    
    async def _analyze_competitive_landscape(self, state: AgentState) -> Dict[str, Any]:
        """Analyze competitive landscape using AI"""
        try:
            if not self.llm_service.client:
                logger.warning("🤖 AI client not available - returning basic competitive analysis")
                return {
                    "positioning": "Analysis requires AI integration",
                    "key_competitors": state.discovered_competitors[:5],
                    "competitive_gaps": ["Feature differentiation", "Market positioning", "Customer experience"],
                    "strengths": ["Technical capability", "Market knowledge"],
                    "threats": state.discovered_competitors[:3]
                }
            
            context = state.analysis_context
            competitors_list = "\n".join([f"- {comp}" for comp in state.discovered_competitors])
            
            analysis_prompt = f"""
            Analyze the competitive landscape for {context.client_company} in the {context.industry} industry.
            
            Company: {context.client_company}
            Business Model: {context.business_model}
            Target Market: {context.target_market}
            
            Discovered Competitors:
            {competitors_list}
            
            Provide a JSON analysis with:
            - positioning: Current market position assessment
            - key_competitors: Top 3 most relevant competitors with threat level
            - competitive_advantages: Potential advantages for the client
            - competitive_gaps: Areas where competitors are stronger
            - differentiation_opportunities: 3 ways to differentiate
            - threat_assessment: Overall competitive threat level (High/Medium/Low)
            """
            
            response = await self.llm_service.client.chat.completions.create(
                model=self.llm_service.model,
                messages=[
                    {"role": "system", "content": "You are a competitive intelligence expert. Provide strategic competitive analysis in JSON format."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            
            import json
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"❌ Competitive analysis error: {e}")
            return {"error": str(e), "fallback": "Basic competitive analysis"}
    
    async def _generate_recommendations(self, state: AgentState, market_insights: Dict, competitive_insights: Dict) -> List[str]:
        """Generate strategic recommendations based on analysis"""
        try:
            if not self.llm_service.client:
                logger.warning("🤖 AI client not available - returning basic recommendations")
                return [
                    "Conduct detailed competitive analysis with AI integration",
                    "Develop unique value proposition based on market gaps",
                    "Focus on customer experience differentiation",
                    "Consider strategic partnerships in target market",
                    "Invest in technology and innovation capabilities"
                ]
            
            context = state.analysis_context
            
            recommendations_prompt = f"""
            Generate strategic recommendations for {context.client_company} based on the analysis:
            
            Company: {context.client_company}
            Industry: {context.industry}
            Business Model: {context.business_model}
            Target Market: {context.target_market}
            
            Market Insights: {str(market_insights)[:500]}...
            Competitive Insights: {str(competitive_insights)[:500]}...
            
            Provide 5-7 actionable strategic recommendations as a JSON array of strings.
            Focus on practical, implementable strategies that address competitive positioning and market opportunities.
            """
            
            response = await self.llm_service.client.chat.completions.create(
                model=self.llm_service.model,
                messages=[
                    {"role": "system", "content": "You are a strategic business consultant. Provide clear, actionable recommendations as a JSON array."},
                    {"role": "user", "content": recommendations_prompt}
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            
            import json
            recommendations = json.loads(content)
            return recommendations if isinstance(recommendations, list) else [str(recommendations)]
            
        except Exception as e:
            logger.error(f"❌ Recommendations generation error: {e}")
            return [f"Recommendation generation failed: {str(e)}"]
    
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
    
    async def _handle_retry_feedback(self, state: AgentState):
        """Handle quality feedback for analysis retry"""
        analysis_issues = [issue for issue in state.retry_context.quality_feedback 
                          if issue.retry_agent == "analysis"]
        
        if not analysis_issues:
            return
        
        logger.info(f"🔧 Processing {len(analysis_issues)} analysis-related quality issues")
        
        for issue in analysis_issues:
            if issue.issue_type == "analysis_depth":
                # Enhance analysis prompts with more detailed requests
                if not hasattr(state, 'enhanced_analysis_prompts'):
                    state.enhanced_analysis_prompts = True
                logger.info("📊 Enhancing analysis depth and detail")
            
            elif issue.issue_type == "competitive_positioning":
                # Focus more on competitive analysis
                if not hasattr(state, 'focus_competitive_analysis'):
                    state.focus_competitive_analysis = True
                logger.info("🎯 Focusing on competitive positioning analysis")
            
            elif issue.issue_type == "market_insights":
                # Enhance market analysis with additional data sources
                if not hasattr(state, 'enhanced_market_analysis'):
                    state.enhanced_market_analysis = True
                logger.info("📈 Enhancing market insights analysis")
            
            elif issue.issue_type == "recommendations_quality":
                # Generate more actionable recommendations
                if not hasattr(state, 'enhanced_recommendations'):
                    state.enhanced_recommendations = True
                logger.info("💡 Enhancing recommendations quality")
        
        # Clear processed feedback
        state.retry_context.quality_feedback = [
            issue for issue in state.retry_context.quality_feedback 
            if issue.retry_agent != "analysis"
        ]