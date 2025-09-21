import hashlib
from typing import Dict, Any, List, Set
from loguru import logger
from models.agent_state import AgentState
from services.tavily_service import TavilyService
from services.redis_service import RedisService


class CompetitorDiscoveryAgent:
    """Agent responsible for discovering competitors using various search strategies"""
    
    def __init__(self, tavily_service: TavilyService, redis_service: RedisService):
        self.name = "competitor_discovery"
        self.tavily_service = tavily_service
        self.redis_service = redis_service
    
    async def process(self, state: AgentState) -> AgentState:
        """Discover competitors using multiple search strategies"""
        try:
            logger.info(f"Starting competitor discovery for {state.analysis_context.client_company}")
            
            # Update progress
            state.update_progress("competitor_discovery", 15)
            
            # Strategy 1: Direct competitor search (critical - must succeed)
            try:
                direct_competitors = await self._discover_direct_competitors(state)
                state.update_progress("competitor_discovery", 30)
            except RuntimeError as e:
                # Critical error - fail the entire workflow
                error_msg = f"Critical failure in competitor discovery: {str(e)}"
                logger.error(error_msg)
                state.add_error(error_msg)
                state.status = "failed"
                return state
            
            # Strategy 2: Industry-based discovery
            industry_competitors = await self._discover_industry_competitors(state)
            state.update_progress("competitor_discovery", 50)
            
            # Strategy 3: Market segment discovery
            segment_competitors = await self._discover_segment_competitors(state)
            state.update_progress("competitor_discovery", 70)
            
            # Strategy 4: Alternative and substitute discovery
            alternative_competitors = await self._discover_alternative_competitors(state)
            state.update_progress("competitor_discovery", 85)
            
            # Consolidate and deduplicate competitors
            all_competitors = self._consolidate_competitors([
                direct_competitors,
                industry_competitors, 
                segment_competitors,
                alternative_competitors
            ])
            
            # Filter and rank competitors
            filtered_competitors = self._filter_and_rank_competitors(
                all_competitors, state.analysis_context
            )
            
            # Update state with discovered competitors
            for competitor in filtered_competitors[:state.analysis_context.max_competitors]:
                # Use extracted_company_name if name is not available
                company_name = competitor.get("name") or competitor.get("extracted_company_name") or "Unknown Company"
                state.add_competitor(company_name)
            
            # Store search results for later processing
            state.search_results["competitor_discovery"] = all_competitors
            
            # Update metadata
            state.metadata.update({
                "total_discovered": len(all_competitors),
                "after_filtering": len(filtered_competitors),
                "selected_for_analysis": len(state.discovered_competitors),
                "discovery_strategies_used": 4
            })
            
            # Complete the stage
            state.complete_stage("competitor_discovery")
            state.update_progress("competitor_discovery", 100)
            
            logger.info(f"Competitor discovery completed. Found {len(state.discovered_competitors)} competitors")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in competitor discovery: {e}")
            state.add_error(f"Competitor discovery failed: {str(e)}")
            return state
    
    async def _discover_direct_competitors(self, state: AgentState) -> List[Dict[str, Any]]:
        """Discover direct competitors using company-specific searches"""
        try:
            context = state.analysis_context
            
            # Check cache first
            cache_key = self._generate_cache_key("direct", context.client_company, context.industry)
            cached_results = await self.redis_service.get_cached_search_results(cache_key)
            
            if cached_results:
                logger.info("Using cached direct competitor results")
                return cached_results
            
            # Perform search
            results = await self.tavily_service.search_competitors(
                company_name=context.client_company,
                industry=context.industry,
                target_market=context.target_market,
                additional_keywords=context.search_keywords[:5]
            )
            
            # Cache results
            await self.redis_service.cache_search_results(cache_key, results)
            
            logger.info(f"Direct competitor search found {len(results)} results")
            return results
            
        except RuntimeError as e:
            # Critical error - propagate up
            logger.error(f"Critical error in direct competitor discovery: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in direct competitor discovery: {e}")
            return []
    
    async def _discover_industry_competitors(self, state: AgentState) -> List[Dict[str, Any]]:
        """Discover competitors by industry analysis"""
        try:
            context = state.analysis_context
            
            # Check cache
            cache_key = self._generate_cache_key("industry", context.industry, context.target_market)
            cached_results = await self.redis_service.get_cached_search_results(cache_key)
            
            if cached_results:
                logger.info("Using cached industry competitor results")
                return cached_results
            
            # Industry-specific search queries
            industry_queries = [
                f"top {context.industry} companies",
                f"leading {context.industry} companies {context.target_market}",
                f"{context.industry} market leaders",
                f"best {context.industry} companies",
                f"{context.industry} industry players"
            ]
            
            all_results = []
            for query in industry_queries:
                results = await self.tavily_service.search_with_custom_query(
                    query=query,
                    search_type="industry_discovery"
                )
                all_results.extend(results)
            
            # Cache results
            await self.redis_service.cache_search_results(cache_key, all_results)
            
            logger.info(f"Industry competitor search found {len(all_results)} results")
            return all_results
            
        except Exception as e:
            logger.error(f"Error in industry competitor discovery: {e}")
            return []
    
    async def _discover_segment_competitors(self, state: AgentState) -> List[Dict[str, Any]]:
        """Discover competitors in specific market segments"""
        try:
            context = state.analysis_context
            
            # Check cache
            cache_key = self._generate_cache_key("segment", context.business_model, context.target_market)
            cached_results = await self.redis_service.get_cached_search_results(cache_key)
            
            if cached_results:
                logger.info("Using cached segment competitor results")
                return cached_results
            
            # Segment-specific queries
            segment_queries = []
            
            # Business model based queries
            if "saas" in context.business_model.lower():
                segment_queries.extend([
                    f"{context.industry} SaaS companies",
                    f"cloud-based {context.industry} solutions",
                    f"subscription {context.industry} platforms"
                ])
            elif "marketplace" in context.business_model.lower():
                segment_queries.extend([
                    f"{context.industry} marketplace platforms",
                    f"online {context.industry} marketplaces",
                    f"peer-to-peer {context.industry} platforms"
                ])
            elif "b2b" in context.business_model.lower():
                segment_queries.extend([
                    f"B2B {context.industry} companies",
                    f"enterprise {context.industry} solutions",
                    f"business {context.industry} services"
                ])
            
            # Target market specific queries
            if context.target_market:
                segment_queries.extend([
                    f"{context.target_market} {context.industry} companies",
                    f"{context.industry} companies serving {context.target_market}"
                ])
            
            all_results = []
            for query in segment_queries[:6]:  # Limit queries
                results = await self.tavily_service.search_with_custom_query(
                    query=query,
                    search_type="segment_discovery"
                )
                all_results.extend(results)
            
            # Cache results
            await self.redis_service.cache_search_results(cache_key, all_results)
            
            logger.info(f"Segment competitor search found {len(all_results)} results")
            return all_results
            
        except Exception as e:
            logger.error(f"Error in segment competitor discovery: {e}")
            return []
    
    async def _discover_alternative_competitors(self, state: AgentState) -> List[Dict[str, Any]]:
        """Discover alternative and substitute competitors"""
        try:
            context = state.analysis_context
            
            # Check cache
            cache_key = self._generate_cache_key("alternatives", context.client_company, context.industry)
            cached_results = await self.redis_service.get_cached_search_results(cache_key)
            
            if cached_results:
                logger.info("Using cached alternative competitor results")
                return cached_results
            
            # Alternative search queries
            alternative_queries = [
                f"alternatives to {context.client_company}",
                f"{context.client_company} competitors alternatives",
                f"similar companies to {context.client_company}",
                f"substitute products for {context.industry}",
                f"emerging {context.industry} companies"
            ]
            
            all_results = []
            for query in alternative_queries:
                results = await self.tavily_service.search_with_custom_query(
                    query=query,
                    search_type="alternative_discovery"
                )
                all_results.extend(results)
            
            # Cache results
            await self.redis_service.cache_search_results(cache_key, all_results)
            
            logger.info(f"Alternative competitor search found {len(all_results)} results")
            return all_results
            
        except Exception as e:
            logger.error(f"Error in alternative competitor discovery: {e}")
            return []
    
    def _consolidate_competitors(self, competitor_lists: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Consolidate and deduplicate competitors from multiple sources"""
        all_competitors = []
        seen_urls = set()
        seen_titles = set()
        
        for competitor_list in competitor_lists:
            for competitor in competitor_list:
                url = competitor.get('url', '')
                title = competitor.get('title', '').lower()
                
                # Skip if we've seen this URL or very similar title
                if url in seen_urls or title in seen_titles:
                    continue
                
                # Skip if title is too generic
                if self._is_generic_title(title):
                    continue
                
                seen_urls.add(url)
                seen_titles.add(title)
                all_competitors.append(competitor)
        
        return all_competitors
    
    def _filter_and_rank_competitors(self, 
                                   competitors: List[Dict[str, Any]], 
                                   context) -> List[Dict[str, Any]]:
        """Filter and rank competitors based on relevance"""
        filtered = []
        
        for competitor in competitors:
            title = competitor.get('title', '').lower()
            content = competitor.get('content', '').lower()
            url = competitor.get('url', '').lower()
            
            # Calculate relevance score
            relevance_score = 0
            
            # Industry keyword matching
            industry_lower = context.industry.lower()
            if industry_lower in title:
                relevance_score += 3
            if industry_lower in content:
                relevance_score += 2
            
            # Target market matching
            if context.target_market:
                target_market_lower = context.target_market.lower()
                if target_market_lower in title:
                    relevance_score += 2
                if target_market_lower in content:
                    relevance_score += 1
            
            # Business model matching
            business_model_lower = context.business_model.lower()
            if business_model_lower in title or business_model_lower in content:
                relevance_score += 2
            
            # Search keyword matching
            for keyword in context.search_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in title:
                    relevance_score += 1
                if keyword_lower in content:
                    relevance_score += 0.5
            
            # Exclude client company itself
            client_company_lower = context.client_company.lower()
            if client_company_lower in title or client_company_lower in url:
                continue
            
            # Filter by minimum relevance score
            if relevance_score >= 1.0:
                competitor["relevance_score"] = relevance_score
                competitor["extracted_company_name"] = self._extract_company_name(competitor)
                filtered.append(competitor)
        
        # Sort by relevance score
        filtered.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return filtered
    
    def _is_generic_title(self, title: str) -> bool:
        """Check if title is too generic to be useful"""
        generic_patterns = [
            "top 10", "best companies", "list of", "directory", 
            "wikipedia", "linkedin", "facebook", "twitter",
            "about us", "contact", "home page"
        ]
        
        title_lower = title.lower()
        return any(pattern in title_lower for pattern in generic_patterns)
    
    def _extract_company_name(self, competitor: Dict[str, Any]) -> str:
        """Extract potential company name from competitor data"""
        title = competitor.get('title', '')
        url = competitor.get('url', '')
        
        # Try to extract from title
        if " - " in title:
            return title.split(" - ")[0].strip()
        elif " | " in title:
            return title.split(" | ")[0].strip()
        elif ":" in title:
            return title.split(":")[0].strip()
        
        # Try to extract from URL domain
        if url:
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if domain:
                    # Remove www. and .com/.org etc.
                    domain = domain.replace('www.', '')
                    domain = domain.split('.')[0]
                    return domain.title()
            except:
                pass
        
        # Fallback to first part of title
        words = title.split()
        if words:
            return words[0]
        
        return "Unknown Company"
    
    def _generate_cache_key(self, strategy: str, *args) -> str:
        """Generate cache key for search results"""
        key_data = f"{strategy}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()