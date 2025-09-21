import asyncio
from typing import Dict, Any, List
from loguru import logger
from models.agent_state import AgentState
from services.tavily_service import TavilyService
from services.redis_service import RedisService


class DataCollectionAgent:
    """Agent responsible for collecting detailed data about discovered competitors"""
    
    def __init__(self, tavily_service: TavilyService, redis_service: RedisService):
        self.name = "data_collection"
        self.tavily_service = tavily_service
        self.redis_service = redis_service
        self.max_concurrent_requests = 3
    
    async def process(self, state: AgentState) -> AgentState:
        """Collect detailed data for each discovered competitor"""
        try:
            logger.info(f"Starting data collection for {len(state.discovered_competitors)} competitors")
            
            # Update progress
            state.update_progress("data_collection", 15)
            
            if not state.discovered_competitors:
                state.add_warning("No competitors found to collect data for")
                state.complete_stage("data_collection")
                return state
            
            # Collect data for each competitor concurrently
            competitor_data = await self._collect_competitor_data_batch(
                state.discovered_competitors, state
            )
            
            # Convert competitor_data dict to list format for search_results
            data_collection_list = []
            for competitor_name, data_points in competitor_data.items():
                data_collection_list.extend(data_points)  # Flatten all data points into a single list
            
            # Store collected data
            state.search_results["data_collection"] = data_collection_list
            
            # Update metadata
            state.metadata.update({
                "competitors_processed": len(competitor_data),
                "data_collection_completed": True,
                "average_data_points": self._calculate_average_data_points(competitor_data)
            })
            
            # Complete the stage
            state.complete_stage("data_collection")
            state.update_progress("data_collection", 100)
            
            logger.info(f"Data collection completed for {len(competitor_data)} competitors")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
            state.add_error(f"Data collection failed: {str(e)}")
            return state
    
    async def _collect_competitor_data_batch(self, 
                                           competitors: List[str], 
                                           state: AgentState) -> Dict[str, List[Dict[str, Any]]]:
        """Collect data for competitors in batches to respect rate limits"""
        competitor_data = {}
        total_competitors = len(competitors)
        
        # Process competitors in batches
        for i in range(0, total_competitors, self.max_concurrent_requests):
            batch = competitors[i:i + self.max_concurrent_requests]
            
            # Update progress
            progress = 15 + int((i / total_competitors) * 80)
            state.update_progress("data_collection", progress)
            
            # Process batch concurrently
            batch_tasks = [
                self._collect_single_competitor_data(competitor, state)
                for competitor in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Store results
            for j, result in enumerate(batch_results):
                competitor_name = batch[j]
                
                if isinstance(result, Exception):
                    logger.error(f"Error collecting data for {competitor_name}: {result}")
                    state.add_warning(f"Failed to collect data for {competitor_name}: {str(result)}")
                    competitor_data[competitor_name] = []
                else:
                    competitor_data[competitor_name] = result
            
            # Add delay between batches to respect rate limits
            if i + self.max_concurrent_requests < total_competitors:
                await asyncio.sleep(2)
        
        return competitor_data
    
    async def _collect_single_competitor_data(self, 
                                            competitor_name: str, 
                                            state: AgentState) -> List[Dict[str, Any]]:
        """Collect detailed data for a single competitor"""
        try:
            # Check cache first
            cached_data = await self.redis_service.get_cached_competitor_data(competitor_name)
            if cached_data:
                logger.info(f"Using cached data for {competitor_name}")
                return cached_data.get("search_results", [])
            
            # Collect data from multiple sources
            all_data = []
            
            # 1. Company details search
            company_details = await self.tavily_service.search_company_details(competitor_name)
            all_data.extend(company_details)
            
            # 2. Additional searches based on context
            context = state.analysis_context
            additional_searches = await self._perform_additional_searches(
                competitor_name, context
            )
            all_data.extend(additional_searches)
            
            # 3. Cache the results
            cache_data = {
                "competitor_name": competitor_name,
                "search_results": all_data,
                "collected_at": str(asyncio.get_event_loop().time())
            }
            await self.redis_service.cache_competitor_data(competitor_name, cache_data)
            
            logger.info(f"Collected {len(all_data)} data points for {competitor_name}")
            return all_data
            
        except Exception as e:
            logger.error(f"Error collecting data for {competitor_name}: {e}")
            raise
    
    async def _perform_additional_searches(self, 
                                         competitor_name: str, 
                                         context) -> List[Dict[str, Any]]:
        """Perform additional targeted searches for specific information"""
        additional_data = []
        
        try:
            # Search for specific information types
            search_queries = [
                f"{competitor_name} business model revenue",
                f"{competitor_name} products services offerings",
                f"{competitor_name} pricing plans costs",
                f"{competitor_name} funding investors valuation",
                f"{competitor_name} team leadership executives",
                f"{competitor_name} recent news updates 2024",
                f"{competitor_name} technology stack platform",
                f"{competitor_name} market position competitors"
            ]
            
            # Limit searches to avoid rate limits
            for query in search_queries[:5]:
                try:
                    results = await self.tavily_service.search_with_custom_query(
                        query=query,
                        search_type="detailed_company_info"
                    )
                    additional_data.extend(results)
                    
                    # Small delay between requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Additional search failed for query '{query}': {e}")
                    continue
            
            return additional_data
            
        except Exception as e:
            logger.error(f"Error in additional searches for {competitor_name}: {e}")
            return []
    
    def _calculate_average_data_points(self, competitor_data: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate average number of data points per competitor"""
        if not competitor_data:
            return 0.0
        
        total_data_points = sum(len(data) for data in competitor_data.values())
        return total_data_points / len(competitor_data)
    
    async def collect_market_data(self, state: AgentState) -> List[Dict[str, Any]]:
        """Collect general market and industry data"""
        try:
            context = state.analysis_context
            
            # Check cache for market data
            cached_market_data = await self.redis_service.get_cached_market_analysis(
                context.industry, context.target_market
            )
            
            if cached_market_data:
                logger.info("Using cached market analysis data")
                return cached_market_data.get("search_results", [])
            
            # Collect fresh market data
            market_data = await self.tavily_service.search_market_analysis(
                industry=context.industry,
                target_market=context.target_market
            )
            
            # Cache the results
            cache_data = {
                "industry": context.industry,
                "target_market": context.target_market,
                "search_results": market_data,
                "collected_at": str(asyncio.get_event_loop().time())
            }
            await self.redis_service.cache_market_analysis(
                context.industry, context.target_market, cache_data
            )
            
            logger.info(f"Collected {len(market_data)} market data points")
            return market_data
            
        except Exception as e:
            logger.error(f"Error collecting market data: {e}")
            return []