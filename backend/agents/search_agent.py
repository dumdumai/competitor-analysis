import hashlib
import asyncio
from typing import Dict, Any, List, Set
from loguru import logger
from models.agent_state import AgentState
from services.tavily_service import TavilyService
from services.redis_service import RedisService
from services.llm_service import LLMService


class SearchAgent:
    """
    Unified agent for competitor discovery and data collection using Tavily search.
    Combines the functionality of competitor_discovery and data_collection agents.
    Uses LLM for intelligent competitor extraction from search results.
    """

    def __init__(self, tavily_service: TavilyService, redis_service: RedisService, llm_service: LLMService):
        self.name = "search_agent"
        self.tavily_service = tavily_service
        self.redis_service = redis_service
        self.llm_service = llm_service
        self.max_concurrent_requests = 3

    async def process(self, state: AgentState) -> AgentState:
        """Execute comprehensive search and data collection"""
        try:
            # Check if this is a retry
            is_retry = state.retry_context.retry_count > 0 and state.retry_context.last_retry_agent == "search"

            if is_retry:
                logger.info(f"🔄 Retrying search (attempt {state.retry_context.retry_count}) for {state.analysis_context.client_company}")
                await self._handle_retry_feedback(state)
            else:
                logger.info(f"🔍 Starting comprehensive search for {state.analysis_context.client_company}")

            # Check if this is a product comparison
            is_product_comparison = state.analysis_context.comparison_type == "product"

            # Update progress
            if is_product_comparison:
                await self._update_progress(state, "search", 5, f"Initializing product search for {state.analysis_context.client_product}")
            else:
                await self._update_progress(state, "search", 5, "Initializing competitor search")

            # Stage 1: Discover competitors or products (enhanced based on feedback)
            if is_product_comparison:
                await self._update_progress(state, "search", 15, "Discovering competing products")
                competitors = await self._discover_products(state)
            else:
                await self._update_progress(state, "search", 15, "Discovering competitors")
                competitors = await self._discover_competitors(state)
                logger.info(f"🔍 DEBUG: _discover_competitors returned: {competitors}")

            if not competitors:
                error_msg = "No competitors found during search"
                logger.warning(f"🔍 DEBUG: {error_msg}")
                state.add_warning(error_msg)
                # Continue with empty list rather than failing
            else:
                logger.info(f"🔍 DEBUG: Found {len(competitors)} competitors: {competitors}")

            # Stage 2: Collect detailed data for top competitors or products
            selected_competitors = competitors[:state.analysis_context.max_competitors]
            logger.info(f"🔍 DEBUG: Selected {len(selected_competitors)} competitors: {selected_competitors}")

            if is_product_comparison:
                await self._update_progress(state, "search", 50, f"Collecting data for {len(selected_competitors)} products")
                competitor_data = await self._collect_product_data(selected_competitors, state)
            else:
                await self._update_progress(state, "search", 50, f"Collecting data for {len(selected_competitors)} competitors")
                competitor_data = await self._collect_competitor_data(selected_competitors, state)
                logger.info(f"🔍 DEBUG: Collected data for {len(competitor_data) if competitor_data else 0} competitors")

            # Stage 3: Store results and update state
            await self._update_progress(state, "search", 90, "Processing and storing results")

            # Update state with discovered competitors or products
            if is_product_comparison:
                for product_name in selected_competitors:
                    state.discovered_products.append(product_name)
                logger.info(f"🔍 DEBUG: Added {len(selected_competitors)} products to state")
            else:
                for competitor_name in selected_competitors:
                    state.add_competitor(competitor_name)
                logger.info(f"🔍 DEBUG: Added {len(selected_competitors)} competitors to state")
                logger.info(f"🔍 DEBUG: State now has {len(state.competitor_data)} total competitors")

            # Store search results (flatten for proper structure)
            all_search_data = []
            for name, data_points in competitor_data.items():
                all_search_data.extend(data_points)

            if is_product_comparison:
                state.search_results["product_search_data"] = all_search_data
            else:
                state.search_results["search_data"] = all_search_data

            # Update metadata
            state.metadata.update({
                "total_discovered": len(competitors),
                "selected_for_analysis": len(selected_competitors),
                "total_data_points": len(all_search_data),
                "search_completed": True,
                "search_retry_count": state.retry_context.retry_count
            })

            # Complete the stage
            state.complete_stage("search")
            await self._update_progress(state, "search", 100, f"Search completed: {len(selected_competitors)} competitors, {len(all_search_data)} data points")

            # If this was a retry, record it
            if is_retry:
                state.record_retry("search", "Quality issues addressed in search")
                logger.info(f"✅ Search retry completed: Found {len(selected_competitors)} competitors with {len(all_search_data)} data points")
            else:
                logger.info(f"✅ Search completed: Found {len(selected_competitors)} competitors with {len(all_search_data)} data points")

            return state

        except Exception as e:
            logger.error(f"❌ Error in search agent: {e}")
            state.add_error(f"Search failed: {str(e)}")
            return state

    async def _discover_competitors(self, state: AgentState) -> List[str]:
        """Discover competitors using a single comprehensive search strategy"""
        context = state.analysis_context

        # Single comprehensive search combining all context
        await self._update_progress(state, "search", 20, "Executing comprehensive competitor search")
        comprehensive_results, search_logs = await self.tavily_service.search_competitors(
            company_name=context.client_company,
            industry=context.industry,
            target_market=context.target_market,
            business_model=context.business_model,
            specific_requirements=context.specific_requirements,
            demo_mode=context.demo_mode,
            max_competitors=context.max_competitors
        )

        # Add search logs to state (but limit stored results to avoid MongoDB 16MB limit)
        from models.agent_state import SearchLog
        for log_dict in search_logs:
            # Truncate results in search log to avoid storing too much data
            truncated_log = log_dict.copy()
            if 'results' in truncated_log and len(truncated_log['results']) > 5:
                truncated_log['results'] = truncated_log['results'][:5]
                truncated_log['processing_notes'] = f"Truncated from {len(log_dict['results'])} to 5 results for storage"
            search_log = SearchLog(**truncated_log)
            state.add_search_log(search_log)

        # Extract competitor names from results using LLM
        await self._update_progress(state, "search", 45, "Analyzing search results for competitors with AI")
        competitors = await self._extract_competitors_from_results(comprehensive_results, context)

        logger.info(f"🔍 Discovered {len(competitors)} potential competitors from comprehensive search")
        return list(competitors)

    async def _collect_competitor_data(self, competitors: List[str], state: AgentState) -> Dict[str, List[Dict[str, Any]]]:
        """Collect detailed data for selected competitors"""
        competitor_data = {}

        for i, competitor_name in enumerate(competitors):
            progress = 50 + (i * 30 // len(competitors))
            await self._update_progress(state, "search", progress, f"Collecting data for {competitor_name}")

            # Search for company details
            company_data, company_search_logs = await self.tavily_service.search_company_details(competitor_name, demo_mode=state.analysis_context.demo_mode)

            # Add search logs to state
            from models.agent_state import SearchLog
            for log_dict in company_search_logs:
                search_log = SearchLog(**log_dict)
                state.add_search_log(search_log)
            competitor_data[competitor_name] = company_data

            # Add delay to respect rate limits
            await asyncio.sleep(0.5)

        return competitor_data

    async def _extract_competitors_from_results(self, results: List[Dict[str, Any]], context) -> Set[str]:
        """Extract competitor names from search results using LLM intelligence"""
        competitors = set()
        client_company_lower = context.client_company.lower()
        max_competitors = context.max_competitors

        # Process results in batches to efficiently use LLM
        batch_size = 3
        max_results_to_process = min(len(results), max_competitors * 3)  # Process more since LLM is smarter

        for i in range(0, max_results_to_process, batch_size):
            batch = results[i:i + batch_size]

            # Stop if we have enough competitors
            if len(competitors) >= max_competitors * 1.5:
                break

            # Extract competitors from this batch using LLM
            batch_competitors = await self._llm_extract_competitors_from_batch(batch, context)

            # Filter out client company and add to main set
            for competitor in batch_competitors:
                if competitor.lower() != client_company_lower and len(competitor) > 2:
                    competitors.add(competitor)

        logger.info(f"🎯 LLM extracted {len(competitors)} competitors from {max_results_to_process} search results (requested: {max_competitors})")
        return competitors

    async def _llm_extract_competitors_from_batch(self, batch: List[Dict[str, Any]], context) -> List[str]:
        """Use LLM to intelligently extract competitor names from a batch of search results"""
        try:
            logger.info(f"🧠 DEBUG: Starting LLM extraction for batch of {len(batch)} results")

            # Prepare the search results content for LLM analysis
            results_content = []
            for i, result in enumerate(batch):
                title = result.get('title', '')
                content = result.get('content', '')[:2000]  # Limit content length
                url = result.get('url', '')

                logger.info(f"🧠 DEBUG: Result {i+1} - Title: {title[:100]}...")
                logger.info(f"🧠 DEBUG: Result {i+1} - Content length: {len(content)}")

                results_content.append(f"""
Result {i+1}:
Title: {title}
URL: {url}
Content: {content}
---
""")

            # Create the LLM prompt for competitor extraction
            prompt = f"""
You are an expert at identifying competitors from web search results.

CONTEXT:
- Client Company: {context.client_company}
- Industry: {context.industry}
- Target Market: {context.target_market}
- Business Model: {context.business_model}

TASK: Analyze the following search results and extract ALL company names that could be competitors to the client company. This includes:
1. Direct competitors (same industry/market)
2. Companies mentioned in comparison articles, "top tools" lists, competitor analysis articles
3. Similar businesses serving the same target market
4. Companies offering similar products/services

IMPORTANT RULES:
- Extract company names, not product names (unless company = product name)
- Include companies from "Best of", "Top X", comparison, and review articles
- Don't skip articles just because they say "best", "top", "comparison" - these often contain the MOST competitors
- Extract multiple companies from single articles when they list competitors
- Skip obvious non-companies (like "AI", "Technology", "Software")
- Return only the company names, one per line

SEARCH RESULTS:
{"".join(results_content)}

COMPETITORS FOUND:
(List company names only, one per line, no explanations)
"""

            logger.info(f"🧠 DEBUG: Prompt length: {len(prompt)} characters")
            logger.info(f"🧠 DEBUG: Calling LLM service...")

            # Call LLM to extract competitors
            if not self.llm_service.client:
                logger.warning("🧠 WARNING: LLM client not initialized, using fallback extraction")
                return self._fallback_extract_competitors(batch, context)

            response = await self.llm_service.client.chat.completions.create(
                model=self.llm_service.model,
                messages=[
                    {"role": "system", "content": "You are an expert at identifying competitors from web search results."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )

            llm_response = response.choices[0].message.content if response.choices else None

            logger.info(f"🧠 DEBUG: LLM response length: {len(llm_response) if llm_response else 0}")
            logger.info(f"🧠 DEBUG: LLM response: {llm_response[:500] if llm_response else 'None'}...")

            # Parse LLM response to extract competitor names
            competitors = []
            if llm_response:
                lines = llm_response.strip().split('\n')
                logger.info(f"🧠 DEBUG: LLM response has {len(lines)} lines")

                for i, line in enumerate(lines):
                    line = line.strip()
                    logger.info(f"🧠 DEBUG: Line {i}: '{line}'")

                    if line and not line.startswith('#') and not line.startswith('-') and len(line) > 2:
                        # Clean up the company name
                        competitor = line.strip(' -•*').title()
                        if competitor and len(competitor) > 2:
                            competitors.append(competitor)
                            logger.info(f"🧠 DEBUG: Added competitor: '{competitor}'")
            else:
                logger.warning(f"🧠 DEBUG: LLM response was empty or None")

            logger.info(f"🧠 LLM extracted {len(competitors)} competitors from batch of {len(batch)} results: {competitors}")
            return competitors

        except Exception as e:
            logger.error(f"🧠 ERROR: LLM competitor extraction failed: {e}")
            import traceback
            logger.error(f"🧠 ERROR: Full traceback: {traceback.format_exc()}")
            # Fallback to basic extraction if LLM fails
            return []

    # Old pattern-matching methods removed - now using LLM for intelligent extraction

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
        """Handle quality feedback for search retry using LLM-provided guidance"""
        # First check for specific search guidance from selected issues
        if state.search_guidance and state.search_guidance.get('retry_suggestions'):
            logger.info(f"🎯 Using targeted search guidance from selected quality issues")
            await self._apply_targeted_search_guidance(state)
            return

        # Fallback to legacy feedback handling
        search_issues = [issue for issue in state.retry_context.quality_feedback
                        if issue.retry_agent == "search"]

        if not search_issues:
            return

        logger.info(f"🔧 Processing {len(search_issues)} search-related quality issues")

        for issue in search_issues:
            if issue.issue_type == "insufficient_competitors":
                # Expand search scope
                state.analysis_context.max_competitors = min(
                    state.analysis_context.max_competitors + 5, 20
                )
                logger.info(f"📈 Expanding max_competitors to {state.analysis_context.max_competitors}")

            elif issue.issue_type == "data_completeness":
                # Add more comprehensive search terms
                if not hasattr(state.analysis_context, 'enhanced_search_terms'):
                    state.analysis_context.enhanced_search_terms = []

                additional_terms = issue.additional_params.get('search_terms', [])
                state.analysis_context.enhanced_search_terms.extend(additional_terms)
                logger.info(f"🔍 Adding enhanced search terms: {additional_terms}")

            elif issue.issue_type == "relevance_low":
                # Focus on specific industry terms
                if issue.additional_params.get('focus_keywords'):
                    state.analysis_context.search_keywords.extend(
                        issue.additional_params['focus_keywords']
                    )
                    logger.info(f"🎯 Adding focus keywords for relevance")

        # Clear processed feedback
        state.retry_context.quality_feedback = [
            issue for issue in state.retry_context.quality_feedback
            if issue.retry_agent != "search"
        ]

    async def _apply_targeted_search_guidance(self, state: AgentState):
        """Apply specific search guidance from LLM quality suggestions"""
        guidance = state.search_guidance
        suggestions = guidance.get('retry_suggestions', [])

        logger.info(f"🎯 Applying {len(suggestions)} targeted search suggestions")

        for suggestion in suggestions:
            issue_type = suggestion.get('issue_type')
            action = suggestion.get('suggestion', '')
            affected_competitors = suggestion.get('affected_competitors', [])

            logger.info(f"🔍 Applying suggestion for {issue_type}: {action}")

            if issue_type == "insufficient_competitors":
                # Apply LLM suggestions for competitor discovery
                if "expand" in action.lower() or "more" in action.lower():
                    state.analysis_context.max_competitors = min(
                        state.analysis_context.max_competitors + 3, 15
                    )

                # Extract any specific search terms suggested by LLM
                search_terms = self._extract_search_terms_from_suggestion(action)
                if search_terms:
                    if not hasattr(state.analysis_context, 'llm_search_terms'):
                        state.analysis_context.llm_search_terms = []
                    state.analysis_context.llm_search_terms.extend(search_terms)
                    logger.info(f"🎯 Added LLM-suggested search terms: {search_terms}")

            elif issue_type == "data_gaps":
                # Store the LLM suggestion for data collection improvements
                state.metadata['llm_data_suggestions'] = action
                logger.info(f"📝 Stored LLM data collection guidance: {action}")

        # Store human feedback for context
        if guidance.get('human_feedback'):
            state.metadata['human_feedback'] = guidance['human_feedback']
            logger.info(f"💬 Human feedback: {guidance['human_feedback']}")

    def _extract_search_terms_from_suggestion(self, suggestion: str) -> List[str]:
        """Extract search terms from LLM suggestion text"""
        terms = []

        # Look for quoted terms in the suggestion
        import re
        quoted_terms = re.findall(r"'([^']*)'|\"([^\"]*)\"", suggestion)
        for match in quoted_terms:
            term = match[0] or match[1]
            if term and len(term.strip()) > 2:  # Only add meaningful terms
                terms.append(term.strip())

        return terms

    async def _discover_products(self, state: AgentState) -> List[str]:
        """Discover competing products using product-specific search strategy"""
        context = state.analysis_context

        # Build product search query
        product_search_query = f"{context.client_product} alternatives competitors {context.product_category}"
        if context.specific_requirements:
            product_search_query += f" {context.specific_requirements}"

        await self._update_progress(state, "search", 20, f"Searching for products similar to {context.client_product}")

        # Search for competing products
        product_results, search_logs = await self.tavily_service.search_products(
            product_name=context.client_product,
            category=context.product_category,
            target_market=context.target_market,
            comparison_criteria=context.comparison_criteria,
            demo_mode=context.demo_mode
        )

        # Add search logs to state (but limit stored results to avoid MongoDB 16MB limit)
        from models.agent_state import SearchLog
        for log_dict in search_logs:
            # Truncate results in search log to avoid storing too much data
            truncated_log = log_dict.copy()
            if 'results' in truncated_log and len(truncated_log['results']) > 5:
                truncated_log['results'] = truncated_log['results'][:5]
                truncated_log['processing_notes'] = f"Truncated from {len(log_dict['results'])} to 5 results for storage"
            search_log = SearchLog(**truncated_log)
            state.add_search_log(search_log)

        # Extract product names from results
        await self._update_progress(state, "search", 45, "Analyzing search results for competing products")
        products = self._extract_products_from_results(product_results, context)

        logger.info(f"🔍 Discovered {len(products)} competing products")
        return list(products)

    async def _collect_product_data(self, products: List[str], state: AgentState) -> Dict[str, List[Dict[str, Any]]]:
        """Collect detailed data for selected products"""
        product_data = {}

        for i, product_name in enumerate(products):
            progress = 50 + (i * 30 // len(products))
            await self._update_progress(state, "search", progress, f"Collecting data for {product_name}")

            # Search for product details including features, pricing, reviews
            product_details, product_search_logs = await self.tavily_service.search_product_details(
                product_name,
                include_features=True,
                include_pricing=True,
                include_reviews=True,
                demo_mode=state.analysis_context.demo_mode
            )

            # Add search logs to state
            from models.agent_state import SearchLog
            for log_dict in product_search_logs:
                search_log = SearchLog(**log_dict)
                state.add_search_log(search_log)

            product_data[product_name] = product_details

            # Add delay to respect rate limits
            await asyncio.sleep(0.5)

        return product_data

    def _extract_products_from_results(self, results: List[Dict[str, Any]], context) -> Set[str]:
        """Extract product names from search results"""
        products = set()
        client_product_lower = context.client_product.lower() if context.client_product else ""

        for result in results:
            title = result.get('title', '')
            content = result.get('content', '')

            # Skip if it's the client product itself
            if client_product_lower and client_product_lower in title.lower():
                continue

            # Extract product names from common patterns
            product_name = self._extract_product_name_from_content(title, content)
            if product_name and len(product_name) > 2:
                products.add(product_name)

        return products

    def _extract_product_name_from_content(self, title: str, content: str) -> str:
        """Extract product name from title and content"""
        # Common patterns for product names
        product_keywords = ['software', 'platform', 'tool', 'app', 'application', 'service', 'solution']

        # Try to extract from title first
        for keyword in product_keywords:
            if keyword in title.lower():
                # Extract the part before the keyword
                parts = title.lower().split(keyword)
                if parts[0].strip():
                    product_name = parts[0].strip().title()
                    # Clean common suffixes
                    for suffix in [' - ', ' | ', ':', ' Inc', ' LLC', ' Corp', ' Ltd']:
                        if suffix in product_name:
                            product_name = product_name.split(suffix)[0].strip()
                    return product_name

        # Fallback to first few words of title
        words = title.split()[:3]
        return ' '.join(words) if words else title[:50]

    def _fallback_extract_competitors(self, batch: List[Dict], context) -> List[str]:
        """Fallback method to extract competitor names without LLM"""
        logger.info(f"🔍 DEBUG: Fallback extraction starting with {len(batch)} search results")
        competitors = set()

        # Simple extraction based on common patterns
        competitor_keywords = ['competitor', 'vs', 'alternative', 'company', 'companies', 'top', 'best']
        industry_terms = context.industry.lower().split() if context.industry else []

        for result in batch:
            title = result.get('title', '').lower()
            content = result.get('content', '').lower()

            # Look for company names in titles containing competitor keywords
            if any(keyword in title for keyword in competitor_keywords):
                # Extract potential company names (capitalized words)
                import re
                title_original = result.get('title', '')
                # Find patterns like "Company Name vs", "Top 10 Companies:", etc.
                company_matches = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC))?\b', title_original)

                for match in company_matches:
                    # Filter out common words
                    if match.lower() not in ['top', 'best', 'companies', 'company', 'inc', 'corp', 'ltd', 'llc']:
                        competitors.add(match.strip())

        # Limit to reasonable number and filter out obvious non-competitors
        result = []
        client_company_lower = context.client_company.lower()

        for comp in list(competitors)[:10]:  # Limit to 10
            if (len(comp) > 2 and
                comp.lower() != client_company_lower and
                len(comp.split()) <= 4):  # Reasonable company name length
                result.append(comp)

        logger.info(f"🔍 DEBUG: Fallback extraction found {len(result)} potential competitors: {result}")
        final_result = result[:context.max_competitors]
        logger.info(f"🔍 DEBUG: Returning {len(final_result)} competitors after max limit: {final_result}")
        return final_result
