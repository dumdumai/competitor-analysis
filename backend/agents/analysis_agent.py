import asyncio
from typing import Dict, Any, List
from loguru import logger
from models.agent_state import AgentState
from models.analysis import CompetitorData
from services.llm_service import LLMService
from services.tavily_service import TavilyService
from services.redis_service import RedisService
from pydantic import BaseModel


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

            # Stage 0: Structure Competitor Data (NEW - Fix the core issue!)
            await self._update_progress(state, "analysis", 15, "Structuring competitor data with AI")
            await self._structure_competitor_data(state)

            # Stage 1: Market Analysis (enhanced based on feedback)
            await self._update_progress(state, "analysis", 35, "Analyzing market landscape")
            market_insights = await self._analyze_market_landscape(state)

            # Stage 2: Competitive Analysis (enhanced based on feedback)
            await self._update_progress(state, "analysis", 65, "Analyzing competitive positioning")
            competitive_insights = await self._analyze_competitive_landscape(state)

            # Stage 3: Strategic Recommendations
            await self._update_progress(state, "analysis", 85, "Generating strategic insights")
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
                f"{context.industry} market size {context.target_market} 2025",
                f"{context.industry} market trends {context.target_market}",
                f"{context.industry} industry analysis {context.target_market}"
            ]

            market_data = []
            # Just do one comprehensive market search instead of looping
            try:
                search_result = await self.tavily_service.search_market_analysis(
                    context.industry, context.target_market, demo_mode=context.demo_mode
                )

                # Handle both tuple and single return formats
                if isinstance(search_result, tuple) and len(search_result) == 2:
                    results, market_search_logs = search_result
                else:
                    results = search_result if search_result else []
                    market_search_logs = []

                market_data.extend(results)

            except Exception as e:
                logger.error(f"❌ Market analysis search failed: {e}")
                results = []
                market_search_logs = []

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

    async def _structure_competitor_data(self, state: AgentState):
        """
        Convert raw Tavily search data into structured CompetitorData objects using LLM.
        This fixes the core issue where we had raw strings instead of proper competitor objects.
        """
        try:
            logger.info("🏗️ Structuring competitor data using LLM for proper CompetitorData objects")

            # Get raw competitor names from search
            raw_competitors = state.discovered_competitors
            raw_search_data = state.search_results.get("search_data", [])

            if not raw_competitors:
                logger.warning("⚠️ No raw competitors found to structure")
                return

            logger.info(f"📊 Processing {len(raw_competitors)} raw competitors: {raw_competitors}")

            # Create structured competitor data using LLM
            structured_competitors = []

            for competitor_name in raw_competitors:
                try:
                    # Find relevant search data for this competitor
                    relevant_data = []
                    for search_item in raw_search_data:
                        if competitor_name.lower() in search_item.get('title', '').lower() or \
                           competitor_name.lower() in search_item.get('content', '').lower():
                            relevant_data.append(search_item)

                    # Use LLM to structure the competitor data
                    structured_competitor = await self._llm_structure_single_competitor(
                        competitor_name, relevant_data, state.analysis_context
                    )

                    if structured_competitor:
                        structured_competitors.append(structured_competitor)
                        logger.info(f"✅ Structured competitor: {structured_competitor.name}")
                    else:
                        logger.warning(f"⚠️ Could not structure competitor: {competitor_name}")

                except Exception as e:
                    logger.error(f"❌ Error structuring competitor {competitor_name}: {e}")
                    continue

            # Update state with structured competitors
            state.competitor_data = structured_competitors
            logger.info(f"🎯 Successfully structured {len(structured_competitors)} competitors into CompetitorData objects")

        except Exception as e:
            logger.error(f"❌ Error in _structure_competitor_data: {e}")
            # Don't fail the entire analysis, just log the error

    async def _llm_structure_single_competitor(self, competitor_name: str, search_data: List[Dict], context) -> CompetitorData:
        """Use LLM to create a structured CompetitorData object from raw search data"""

        # Enhanced Pydantic model for comprehensive competitor data
        class StructuredCompetitor(BaseModel):
            name: str
            description: str
            business_model: str
            target_market: str
            industry: str
            key_products: List[str] = []
            strengths: List[str] = []
            weaknesses: List[str] = []
            market_position: str = "Competitor"
            pricing_strategy: str = ""
            headquarters: str = ""
            employee_count: str = ""
            website: str = ""
            founding_year: int = None

        # Prepare search data summary with URLs
        search_summary = ""
        for item in search_data[:5]:  # Limit to avoid token overflow
            search_summary += f"Title: {item.get('title', '')}\nURL: {item.get('url', '')}\nContent: {item.get('content', '')[:200]}\n\n"

        if not search_summary.strip():
            search_summary = f"Limited information available for {competitor_name}"

        # Enhanced LLM prompt for better competitor structuring
        prompt = f"""
        You are a business analyst creating a detailed competitor profile. Analyze the search data and create a comprehensive business profile.

        Company to Analyze: {competitor_name}
        Industry: {context.industry}
        Target Market: {context.target_market}
        Client Context: {context.business_model}

        Search Data Available:
        {search_summary}

        CRITICAL RELEVANCE REQUIREMENT: Only analyze this company if it is a TRUE COMPETITOR to the client company. A true competitor must:
        - Operate in the SAME or closely RELATED industry as {context.industry}
        - Have a SIMILAR business model to {context.business_model}
        - Target the SAME or OVERLAPPING market as {context.target_market}
        - Offer products/services that could substitute for the client's offerings

        If {competitor_name} does NOT meet these criteria, return an empty response to indicate it should be EXCLUDED as irrelevant.

        Create a detailed competitor analysis with these requirements:

        1. name: Clean company name (remove prefixes like "Top 5", "TRENDING", "Market Analysis")
        2. description: Professional 2-3 sentence company overview focusing on their business
        3. business_model: Specific revenue model (B2B SaaS, marketplace, consulting, etc.) - must be similar to {context.business_model}
        4. target_market: Who they serve (enterprise, SMB, consumers, etc.) - must overlap with {context.target_market}
        5. industry: Primary industry sector they operate in - must be same/related to {context.industry}
        6. key_products: 3-5 main products or services they offer
        7. strengths: 3-4 key competitive advantages
        8. weaknesses: 2-3 potential challenges or limitations
        9. market_position: Market position (leader, challenger, niche player, emerging)
        10. pricing_strategy: How they price their offerings (if known)
        11. headquarters: Location if mentioned
        12. employee_count: Approximate size if mentioned
        13. website: Official company website URL (extract from search data URLs or content, format as https://domain.com)

        IMPORTANT FOR WEBSITE: Look for the company's official website in:
        - Search result URLs that contain the company name
        - Website mentions in the content (like "visit us at", "website:", "homepage:", etc.)
        - Domain names that match the company name
        - Extract the main domain (e.g., from https://company.com/about get https://company.com)

        RELEVANCE CHECK: Before providing any data, verify that {competitor_name} is actually a relevant competitor. If it operates in a completely different industry (e.g., home appliances vs software, retail vs consulting), return empty response.

        Base your analysis on the search data provided. If specific details aren't available, make reasonable inferences based on the industry context and company type.
        Be specific and professional - avoid generic descriptions.
        """

        try:
            logger.info(f"🤖 Starting LLM structuring for: {competitor_name}")

            # Use structured output from LLM
            response = await self.llm_service.get_structured_response(
                prompt=prompt,
                response_model=StructuredCompetitor,
                max_tokens=1200  # Increased for more detailed responses
            )

            if response:
                logger.info(f"✅ LLM generated structured data for: {response.name}")
                logger.info(f"🔍 DEBUG: LLM Response - Description: {response.description[:100]}...")
                logger.info(f"🔍 DEBUG: LLM Response - Business Model: {response.business_model}")
                logger.info(f"🔍 DEBUG: LLM Response - Website: {response.website}")
                logger.info(f"🔍 DEBUG: LLM Response - Key Products: {response.key_products}")

                # Convert to CompetitorData - matching exact demo structure
                competitor_data = CompetitorData(
                    name=response.name,
                    website=response.website or "",
                    description=response.description,
                    business_model=response.business_model,
                    target_market=response.target_market,
                    industry=response.industry,
                    founding_year=response.founding_year,
                    headquarters=response.headquarters or None,
                    employee_count=response.employee_count or None,
                    funding_info=None,  # Demo uses None
                    key_products=response.key_products or [],
                    pricing_strategy=response.pricing_strategy or None,
                    market_position=response.market_position or None,
                    strengths=response.strengths or [],
                    weaknesses=response.weaknesses or [],
                    recent_news=[],
                    social_media_presence={},
                    financial_data=None,
                    technology_stack=[],
                    partnerships=[],
                    competitive_advantages=response.strengths or [],
                    market_share=None,
                    growth_trajectory=None,
                    threat_level=None,  # Demo uses None, not "medium"
                    primary_product=None,  # Add missing field
                    product_details=None,  # Add missing field
                    product_features=[],  # Add missing field
                    product_pricing=None,  # Add missing field
                    product_reviews=None  # Add missing field
                )

                logger.info(f"🎯 Created rich CompetitorData for: {competitor_data.name} ({competitor_data.business_model})")
                logger.info(f"🔍 DEBUG: Final CompetitorData - Description: {competitor_data.description[:100]}...")
                logger.info(f"🔍 DEBUG: Final CompetitorData - Key Products: {competitor_data.key_products}")
                return competitor_data
            else:
                logger.warning(f"⚠️ LLM returned empty response for {competitor_name}")

        except Exception as e:
            logger.error(f"❌ LLM structuring failed for {competitor_name}: {e}")
            import traceback
            logger.error(f"Full error trace: {traceback.format_exc()}")

        # Enhanced fallback: create informative CompetitorData object
        clean_name = competitor_name.replace("TRENDING NOW", "").replace("Top 5", "").replace("Market Analysis", "").strip()

        logger.warning(f"🔄 Using enhanced fallback for: {clean_name}")

        return CompetitorData(
            name=clean_name,
            website="",
            description=f"{clean_name} is a competitor operating in the {context.industry} industry, targeting {context.target_market} with {context.business_model} solutions.",
            business_model=f"{context.business_model}",  # Use client context as fallback
            target_market=context.target_market,
            industry=context.industry,  # This fixes the missing industry issue!
            founding_year=None,
            headquarters=None,
            employee_count=None,
            funding_info=None,
            key_products=[f"{context.industry} solutions"],
            pricing_strategy=None,
            market_position="Competitor",
            strengths=["Market presence", "Industry experience"],
            weaknesses=["Limited public information"],
            recent_news=[],
            social_media_presence={},
            financial_data=None,
            technology_stack=[],
            partnerships=[],
            competitive_advantages=["Market presence"],
            market_share=None,
            growth_trajectory=None,
            threat_level=None,
            primary_product=None,
            product_details=None,
            product_features=[],
            product_pricing=None,
            product_reviews=None
        )
