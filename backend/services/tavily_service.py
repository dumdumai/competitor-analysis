import os
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from tavily import TavilyClient
from loguru import logger
import json
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv(dotenv_path='/app/backend/.env')


class TavilyService:
    """Service for handling Tavily API interactions"""
    
    def __init__(self):
        # Initialize API client (not demo mode - that's per-request)
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                self.client = TavilyClient(api_key=self.api_key)
                logger.info("Tavily client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {e}")
                self.client = None
        else:
            logger.warning("TAVILY_API_KEY not provided - will use demo mode when requested")
        
        self.max_results = int(os.getenv("TAVILY_MAX_RESULTS", "10"))
        self.search_depth = os.getenv("TAVILY_SEARCH_DEPTH", "advanced")
        self.include_domains = self._parse_domains(os.getenv("TAVILY_INCLUDE_DOMAINS", ""))
        self.exclude_domains = self._parse_domains(os.getenv("TAVILY_EXCLUDE_DOMAINS", ""))
    
    def _parse_domains(self, domains_str: str) -> List[str]:
        """Parse comma-separated domains string into list"""
        if not domains_str:
            return []
        return [domain.strip() for domain in domains_str.split(",") if domain.strip()]
    
    async def search_competitors(self, 
                               company_name: str, 
                               industry: str, 
                               target_market: str = "",
                               business_model: str = "",
                               specific_requirements: str = "",
                               additional_keywords: List[str] = None,
                               demo_mode: bool = False,
                               max_competitors: int = 10) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Search for competitors using various search strategies"""
        
        # Use demo mode if requested or client unavailable
        if demo_mode or not self.client:
            logger.info(f"Using demo mode for competitor search (demo_mode={demo_mode}, client_available={self.client is not None})")
            results = await self._get_demo_competitor_data(company_name, industry, target_market)
            # Create demo search log
            search_log = {
                "search_type": "competitor_search",
                "query": f"{company_name} competitors {industry} {target_market}",
                "parameters": {
                    "max_results": self.max_results,
                    "search_depth": self.search_depth,
                    "demo_mode": True
                },
                "results_count": len(results),
                "results": results,
                "processing_notes": "Demo mode - using mock data",
                "duration_ms": 500
            }
            return results, [search_log]
        
        try:
            search_queries = self._generate_competitor_search_queries(
                company_name, industry, target_market, business_model, specific_requirements, additional_keywords
            )
            
            # LIMIT QUERIES TO AVOID RESOURCE WASTE
            # Only use first 2 queries for efficiency (should give us enough results)
            search_queries = search_queries[:2]
            
            all_results = []
            search_logs = []
            
            for query in search_queries:
                logger.info(f"Searching with query: {query}")
                start_time = time.time()
                
                search_log = {
                    "search_type": "competitor_search",
                    "query": query,
                    "parameters": {
                        "max_results": self.max_results,
                        "search_depth": self.search_depth,
                        "include_domains": self.include_domains,
                        "exclude_domains": self.exclude_domains
                    }
                }
                
                try:
                    # Use asyncio to make the sync call non-blocking
                    results = await asyncio.to_thread(
                        self.client.search,
                        query=query,
                        search_depth=self.search_depth,
                        max_results=self.max_results,
                        include_domains=self.include_domains,
                        exclude_domains=self.exclude_domains,
                        include_raw_content=True
                    )
                    
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    if results and "results" in results:
                        for result in results["results"]:
                            result["search_query"] = query
                            result["search_type"] = "competitor_search"
                        all_results.extend(results["results"])
                        
                        search_log["results_count"] = len(results["results"])
                        search_log["results"] = results["results"]
                        search_log["duration_ms"] = duration_ms
                        search_log["processing_notes"] = f"Successfully retrieved {len(results['results'])} results"
                    else:
                        search_log["results_count"] = 0
                        search_log["results"] = []
                        search_log["duration_ms"] = duration_ms
                        search_log["processing_notes"] = "No results returned"
                    
                    search_logs.append(search_log)
                    
                    # Add delay to respect rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {e}")
                    search_log["error"] = str(e)
                    search_log["results_count"] = 0
                    search_log["results"] = []
                    search_log["duration_ms"] = int((time.time() - start_time) * 1000)
                    search_logs.append(search_log)
                    continue
            
            # Remove duplicates based on URL
            unique_results = {}
            for result in all_results:
                url = result.get("url", "")
                if url and url not in unique_results:
                    unique_results[url] = result
            
            logger.info(f"Found {len(unique_results)} unique results for competitor search")
            return list(unique_results.values()), search_logs
            
        except Exception as e:
            logger.error(f"Error in competitor search: {e}")
            error_log = {
                "search_type": "competitor_search",
                "query": f"Failed search for {company_name}",
                "parameters": {},
                "results_count": 0,
                "results": [],
                "error": str(e),
                "processing_notes": "Search operation failed"
            }
            return [], [error_log]
    
    async def search_company_details(self, company_name: str, demo_mode: bool = False) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Search for detailed information about a specific company"""
        
        # Use demo mode if requested or client unavailable
        if demo_mode or not self.client:
            logger.info(f"Using demo mode for company details (demo_mode={demo_mode}, client_available={self.client is not None})")
            results = await self._get_demo_company_details(company_name)
            search_log = {
                "search_type": "company_details",
                "query": f"{company_name} company profile",
                "parameters": {"demo_mode": True},
                "results_count": len(results),
                "results": results,
                "processing_notes": "Demo mode - using mock data",
                "duration_ms": 300
            }
            return results, [search_log]
        
        try:
            search_queries = self._generate_company_detail_queries(company_name)
            
            all_results = []
            search_logs = []
            
            for query in search_queries:
                logger.info(f"Searching company details with query: {query}")
                start_time = time.time()
                
                search_log = {
                    "search_type": "company_details",
                    "query": query,
                    "parameters": {
                        "max_results": self.max_results,
                        "search_depth": self.search_depth
                    }
                }
                
                try:
                    results = await asyncio.to_thread(
                        self.client.search,
                        query=query,
                        search_depth=self.search_depth,
                        max_results=self.max_results,
                        include_domains=self.include_domains,
                        exclude_domains=self.exclude_domains,
                        include_raw_content=True
                    )
                    
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    if results and "results" in results:
                        for result in results["results"]:
                            result["search_query"] = query
                            result["search_type"] = "company_details"
                        all_results.extend(results["results"])
                        
                        search_log["results_count"] = len(results["results"])
                        search_log["results"] = results["results"]
                        search_log["duration_ms"] = duration_ms
                        search_log["processing_notes"] = f"Retrieved {len(results['results'])} company details"
                    else:
                        search_log["results_count"] = 0
                        search_log["results"] = []
                        search_log["duration_ms"] = duration_ms
                        search_log["processing_notes"] = "No company details found"
                    
                    search_logs.append(search_log)
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Company detail search failed for query '{query}': {e}")
                    search_log["error"] = str(e)
                    search_log["results_count"] = 0
                    search_log["results"] = []
                    search_log["duration_ms"] = int((time.time() - start_time) * 1000)
                    search_logs.append(search_log)
                    continue
            
            # Remove duplicates
            unique_results = {}
            for result in all_results:
                url = result.get("url", "")
                if url and url not in unique_results:
                    unique_results[url] = result
            
            logger.info(f"Found {len(unique_results)} unique results for {company_name}")
            return list(unique_results.values()), search_logs
            
        except Exception as e:
            logger.error(f"Error searching company details for {company_name}: {e}")
            error_log = {
                "search_type": "company_details",
                "query": f"Failed search for {company_name}",
                "parameters": {},
                "results_count": 0,
                "results": [],
                "error": str(e),
                "processing_notes": "Company details search failed"
            }
            return [], [error_log]
    
    async def search_market_analysis(self, 
                                   industry: str, 
                                   target_market: str = "",
                                   year: str = "2024",
                                   demo_mode: bool = False) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Search for market analysis and industry reports"""
        
        # Use demo mode if requested or client unavailable
        if demo_mode or not self.client:
            logger.info(f"Using demo mode for market analysis (demo_mode={demo_mode}, client_available={self.client is not None})")
            results = await self._get_demo_market_data(industry, target_market, year)
            search_log = {
                "search_type": "market_analysis",
                "query": f"{industry} market analysis {target_market} {year}",
                "parameters": {"demo_mode": True},
                "results_count": len(results),
                "results": results,
                "processing_notes": "Demo mode - using mock market data",
                "duration_ms": 400
            }
            return results, [search_log]
        
        try:
            search_queries = self._generate_market_analysis_queries(industry, target_market, year)
            
            all_results = []
            
            for query in search_queries:
                logger.info(f"Searching market analysis with query: {query}")
                
                try:
                    results = await asyncio.to_thread(
                        self.client.search,
                        query=query,
                        search_depth=self.search_depth,
                        max_results=self.max_results,
                        include_domains=self.include_domains,
                        exclude_domains=self.exclude_domains,
                        include_raw_content=True
                    )
                    
                    if results and "results" in results:
                        for result in results["results"]:
                            result["search_query"] = query
                            result["search_type"] = "market_analysis"
                        all_results.extend(results["results"])
                    
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Market analysis search failed for query '{query}': {e}")
                    continue
            
            # Remove duplicates
            unique_results = {}
            for result in all_results:
                url = result.get("url", "")
                if url and url not in unique_results:
                    unique_results[url] = result
            
            logger.info(f"Found {len(unique_results)} unique market analysis results")
            return list(unique_results.values())
            
        except Exception as e:
            logger.error(f"Error in market analysis search: {e}")
            return []
    
    def _generate_competitor_search_queries(self, 
                                          company_name: str, 
                                          industry: str, 
                                          target_market: str = "",
                                          business_model: str = "",
                                          specific_requirements: str = "",
                                          additional_keywords: List[str] = None) -> List[str]:
        """Generate comprehensive, focused search queries combining all context"""
        additional_keywords = additional_keywords or []
        
        # Extract key technical/functional terms from requirements
        requirement_terms = self._extract_key_terms_from_requirements(specific_requirements)
        
        # Build comprehensive search queries that combine all context
        comprehensive_queries = []
        
        # Priority 1: Highly specific queries combining all available context
        if business_model and requirement_terms:
            comprehensive_queries.extend([
                f"{' '.join(requirement_terms)} {business_model} {industry} competitors {target_market}",
                f"{industry} {business_model} companies {' '.join(requirement_terms)} competitive analysis",
                f"top {' '.join(requirement_terms)} {industry} {business_model} providers {target_market} 2024"
            ])
        
        # Priority 2: Business model + industry + market specific
        if business_model:
            comprehensive_queries.extend([
                f"{business_model} {industry} market leaders {target_market} competitive landscape",
                f"leading {business_model} {industry} companies {target_market} analysis 2024"
            ])
        
        # Priority 3: Requirement-driven competitor searches
        if requirement_terms:
            comprehensive_queries.extend([
                f"{' '.join(requirement_terms)} {industry} companies market share analysis",
                f"best {' '.join(requirement_terms)} {industry} solutions {target_market}"
            ])
        
        # Priority 4: Direct competitive analysis queries
        comprehensive_queries.extend([
            f"{company_name} competitors {industry} {business_model} {target_market}",
            f"{industry} competitive intelligence {business_model} market analysis 2024"
        ])
        
        # Priority 5: Alternative and comparison queries (most targeted)
        if business_model and requirement_terms:
            comprehensive_queries.append(
                f"alternatives to {company_name} {' '.join(requirement_terms)} {industry} {business_model}"
            )
        
        # Filter out empty or too generic queries
        filtered_queries = []
        for query in comprehensive_queries:
            # Remove extra spaces and ensure minimum specificity
            clean_query = ' '.join(query.split())
            if len(clean_query.split()) >= 4:  # Ensure queries have enough specificity
                filtered_queries.append(clean_query)
        
        # Return top 6 most specific queries to avoid rate limits while maintaining quality
        return filtered_queries[:6]
    
    async def search_products(self,
                             product_name: str,
                             category: str,
                             target_market: str = "",
                             comparison_criteria: List[str] = None,
                             demo_mode: bool = False) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Search for competing products"""
        
        # Use demo mode if requested or client unavailable
        if demo_mode or not self.client:
            logger.info(f"Using demo mode for product search (demo_mode={demo_mode}, client_available={self.client is not None})")
            results = await self._get_demo_product_data(product_name, category)
            # Create demo search log
            search_log = {
                "search_type": "product_search",
                "query": f"{product_name} alternatives {category}",
                "parameters": {
                    "max_results": self.max_results,
                    "search_depth": self.search_depth,
                    "demo_mode": True
                },
                "results_count": len(results),
                "results": results,
                "processing_notes": "Demo mode - using mock product data",
                "duration_ms": 500
            }
            return results, [search_log]
        
        try:
            # Generate product-specific search queries
            search_queries = self._generate_product_search_queries(
                product_name, category, target_market, comparison_criteria
            )
            
            all_results = []
            search_logs = []
            
            for query in search_queries:
                logger.info(f"Searching for products with query: {query}")
                start_time = time.time()
                
                search_log = {
                    "search_type": "product_search",
                    "query": query,
                    "parameters": {
                        "max_results": self.max_results,
                        "search_depth": self.search_depth
                    }
                }
                
                try:
                    results = await asyncio.to_thread(
                        self.client.search,
                        query=query,
                        max_results=self.max_results,
                        search_depth=self.search_depth
                    )
                    
                    if results and 'results' in results:
                        all_results.extend(results['results'])
                        search_log["results_count"] = len(results['results'])
                        search_log["results"] = results['results']
                    
                except Exception as e:
                    logger.error(f"Search query failed: {e}")
                    search_log["error"] = str(e)
                
                search_log["duration_ms"] = int((time.time() - start_time) * 1000)
                search_logs.append(search_log)
                
                # Rate limit protection
                await asyncio.sleep(0.5)
            
            return all_results, search_logs
            
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return [], [{
                "search_type": "product_search",
                "error": str(e)
            }]
    
    async def search_product_details(self,
                                    product_name: str,
                                    include_features: bool = True,
                                    include_pricing: bool = True,
                                    include_reviews: bool = True,
                                    demo_mode: bool = False) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Search for detailed product information"""
        
        if demo_mode or not self.client:
            logger.info(f"Using demo mode for product details (demo_mode={demo_mode}, client_available={self.client is not None})")
            results = await self._get_demo_product_details(product_name)
            search_log = {
                "search_type": "product_details",
                "query": f"{product_name} features pricing reviews",
                "parameters": {"demo_mode": True},
                "results_count": len(results),
                "results": results,
                "duration_ms": 300
            }
            return results, [search_log]
        
        try:
            queries = []
            if include_features:
                queries.append(f"{product_name} features specifications capabilities")
            if include_pricing:
                queries.append(f"{product_name} pricing plans cost subscription")
            if include_reviews:
                queries.append(f"{product_name} reviews ratings user feedback")
            
            all_results = []
            search_logs = []
            
            for query in queries:
                logger.info(f"Searching product details: {query}")
                start_time = time.time()
                
                search_log = {
                    "search_type": "product_details",
                    "query": query,
                    "parameters": {
                        "max_results": self.max_results,
                        "search_depth": self.search_depth
                    }
                }
                
                try:
                    results = await asyncio.to_thread(
                        self.client.search,
                        query=query,
                        max_results=self.max_results,
                        search_depth=self.search_depth
                    )
                    
                    if results and 'results' in results:
                        all_results.extend(results['results'])
                        search_log["results_count"] = len(results['results'])
                        search_log["results"] = results['results']
                    
                except Exception as e:
                    logger.error(f"Product details search failed: {e}")
                    search_log["error"] = str(e)
                
                search_log["duration_ms"] = int((time.time() - start_time) * 1000)
                search_logs.append(search_log)
                
                await asyncio.sleep(0.5)
            
            return all_results, search_logs
            
        except Exception as e:
            logger.error(f"Product details search failed: {e}")
            return [], [{
                "search_type": "product_details",
                "error": str(e)
            }]
    
    def _generate_product_search_queries(self,
                                        product_name: str,
                                        category: str,
                                        target_market: str,
                                        comparison_criteria: List[str]) -> List[str]:
        """Generate search queries for product discovery"""
        queries = [
            f"{product_name} alternatives {category}",
            f"best {category} software like {product_name}",
            f"{product_name} competitors comparison {category}",
            f"top {category} tools similar to {product_name}"
        ]
        
        if target_market:
            queries.append(f"{category} solutions for {target_market} {product_name} alternatives")
        
        if comparison_criteria:
            for criterion in comparison_criteria[:2]:  # Limit to avoid too many queries
                queries.append(f"{product_name} vs competitors {criterion} {category}")
        
        return queries[:5]  # Limit total queries
    
    async def _get_demo_product_data(self, product_name: str, category: str) -> List[Dict[str, Any]]:
        """Return demo product data for testing"""
        demo_products = [
            {
                "title": "Slack - Team Communication Platform",
                "url": "https://slack.com",
                "content": "Slack is a messaging platform for teams that brings communication together",
                "score": 0.95
            },
            {
                "title": "Microsoft Teams - Collaboration Hub",
                "url": "https://teams.microsoft.com",
                "content": "Microsoft Teams combines chat, video meetings, and file collaboration",
                "score": 0.93
            },
            {
                "title": "Discord - Communication Platform",
                "url": "https://discord.com",
                "content": "Discord offers voice, video, and text communication for communities",
                "score": 0.90
            }
        ]
        return demo_products
    
    async def _get_demo_product_details(self, product_name: str) -> List[Dict[str, Any]]:
        """Return demo product details for testing"""
        return [
            {
                "title": f"{product_name} Features and Capabilities",
                "content": "Core features include real-time messaging, file sharing, integrations",
                "score": 0.95
            },
            {
                "title": f"{product_name} Pricing Plans",
                "content": "Free tier available, Pro plan at $12/user/month, Enterprise custom pricing",
                "score": 0.92
            },
            {
                "title": f"{product_name} User Reviews",
                "content": "4.5/5 stars average rating, praised for ease of use and reliability",
                "score": 0.90
            }
        ]
    
    def _extract_key_terms_from_requirements(self, specific_requirements: str) -> List[str]:
        """Extract key technical and functional terms from requirements"""
        if not specific_requirements:
            return []
        
        req_lower = specific_requirements.lower()
        key_terms = []
        
        # Technology terms
        tech_terms = {
            'ai': 'AI-powered',
            'artificial intelligence': 'AI-powered', 
            'machine learning': 'ML-enabled',
            'automation': 'automation',
            'cloud': 'cloud-based',
            'saas': 'SaaS',
            'platform': 'platform',
            'integration': 'integration',
            'analytics': 'analytics',
            'data': 'data-driven',
            'enterprise': 'enterprise',
            'b2b': 'B2B',
            'workflow': 'workflow',
            'crm': 'CRM',
            'erp': 'ERP',
            'api': 'API-enabled'
        }
        
        # Find matching terms
        for term, normalized in tech_terms.items():
            if term in req_lower:
                if normalized not in key_terms:
                    key_terms.append(normalized)
        
        return key_terms[:3]  # Limit to top 3 most relevant terms
    
    def _generate_company_detail_queries(self, company_name: str) -> List[str]:
        """Generate search queries for company details - LIMITED to reduce API calls"""
        # REDUCED from 8 to 2 queries to save Tavily API resources
        # These 2 comprehensive queries should capture most important info
        return [
            f"{company_name} company profile overview business model products",
            f"{company_name} funding revenue recent news competitors"
        ]
    
    def _generate_market_analysis_queries(self, 
                                        industry: str, 
                                        target_market: str = "",
                                        year: str = "2024") -> List[str]:
        """Generate search queries for market analysis"""
        base_queries = [
            f"{industry} market analysis {year}",
            f"{industry} industry report {year}",
            f"{industry} market size trends {year}",
            f"{industry} market research {year}",
            f"{industry} industry outlook {year}"
        ]
        
        if target_market:
            base_queries.extend([
                f"{industry} market analysis {target_market} {year}",
                f"{target_market} {industry} industry report {year}",
                f"{industry} market size {target_market} {year}"
            ])
        
        return base_queries
    
    async def search_with_custom_query(self, 
                                     query: str, 
                                     search_type: str = "custom",
                                     demo_mode: bool = False) -> List[Dict[str, Any]]:
        """Perform a custom search with the given query"""
        
        # Use demo mode if requested or client unavailable
        if demo_mode or not self.client:
            logger.info(f"Using demo mode for custom search (demo_mode={demo_mode}, client_available={self.client is not None})")
            return await self._get_demo_custom_search(query, search_type)
        
        try:
            logger.info(f"Custom search with query: {query}")
            
            results = await asyncio.to_thread(
                self.client.search,
                query=query,
                search_depth=self.search_depth,
                max_results=self.max_results,
                include_domains=self.include_domains,
                exclude_domains=self.exclude_domains,
                include_raw_content=True
            )
            
            if results and "results" in results:
                for result in results["results"]:
                    result["search_query"] = query
                    result["search_type"] = search_type
                return results["results"]
            
            return []
            
        except Exception as e:
            logger.error(f"Error in custom search '{query}': {e}")
            return []
    
    async def _get_demo_competitor_data(self, company_name: str, industry: str, target_market: str) -> List[Dict[str, Any]]:
        """Generate demo competitor data when real API is unavailable"""
        
        # Industry-specific competitor templates
        competitor_templates = {
            "Technology": [
                "Microsoft", "Google", "Amazon", "Apple", "Meta", "IBM", "Oracle", "Salesforce", "Adobe", "Intel"
            ],
            "Healthcare": [
                "Johnson & Johnson", "Pfizer", "UnitedHealth Group", "Merck", "AbbVie", "Bristol Myers Squibb", "Eli Lilly", "Amgen", "Gilead Sciences", "Moderna"
            ],
            "Finance": [
                "JPMorgan Chase", "Bank of America", "Wells Fargo", "Citigroup", "Goldman Sachs", "Morgan Stanley", "American Express", "Capital One", "Visa", "Mastercard"
            ],
            "E-commerce": [
                "Amazon", "Shopify", "eBay", "Etsy", "Wayfair", "Target", "Walmart", "Best Buy", "Home Depot", "Costco"
            ],
            "Education": [
                "Pearson", "McGraw Hill", "Cengage Learning", "Blackboard", "Canvas", "Coursera", "edX", "Udemy", "Khan Academy", "Duolingo"
            ]
        }
        
        # Get relevant competitors for the industry
        competitors = competitor_templates.get(industry, [
            "GlobalCorp", "InnovateTech", "MarketLeader", "IndustryGiant", "CompetitorOne"
        ])
        
        # Generate demo data
        demo_results = []
        for i, competitor in enumerate(competitors[:6]):  # Limit to 6 competitors
            demo_results.append({
                "title": f"{competitor} - Leading {industry} Company",
                "url": f"https://{competitor.lower().replace(' ', '')}.com",
                "content": f"{competitor} is a major player in the {industry} industry, serving {target_market} with innovative solutions. The company offers comprehensive {industry.lower()} services and has established itself as a key competitor in the market.",
                "score": 0.8 - (i * 0.1),  # Decreasing relevance scores
                "search_query": f"{company_name} competitors {industry}",
                "search_type": "demo_mode"
            })
        
        # Add a few industry-specific results
        demo_results.extend([
            {
                "title": f"{industry} Market Analysis 2024",
                "url": f"https://marketresearch.com/{industry.lower()}-analysis",
                "content": f"Comprehensive analysis of the {industry} market in {target_market}. Market size, trends, and competitive landscape overview.",
                "score": 0.9,
                "search_query": f"{industry} market analysis",
                "search_type": "demo_mode"
            },
            {
                "title": f"Top {industry} Companies in {target_market}",
                "url": f"https://industryreport.com/top-{industry.lower()}-companies",
                "content": f"List of leading {industry} companies operating in {target_market}, including market share and competitive positioning.",
                "score": 0.85,
                "search_query": f"top {industry} companies {target_market}",
                "search_type": "demo_mode"
            }
        ])
        
        logger.info(f"Generated {len(demo_results)} demo competitor records for {industry} industry")
        
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        return demo_results
    
    async def _get_demo_market_data(self, industry: str, target_market: str, year: str) -> List[Dict[str, Any]]:
        """Generate demo market analysis data when real API is unavailable"""
        
        demo_results = [
            {
                "title": f"{industry} Market Analysis {year} - Industry Report",
                "url": f"https://marketresearch.com/{industry.lower()}-analysis-{year}",
                "content": f"The {industry} market in {target_market} showed strong growth in {year}. Market trends indicate increasing demand for innovative solutions, with digital transformation being a key driver. Major players are focusing on strategic partnerships and technological advancement.",
                "score": 0.95,
                "search_query": f"{industry} market analysis {year}",
                "search_type": "demo_market_analysis"
            },
            {
                "title": f"{industry} Industry Outlook {year} - Growth Projections",
                "url": f"https://industryinsights.com/{industry.lower()}-outlook-{year}",
                "content": f"The {industry} industry is projected to experience significant growth over the next 5 years. Key factors driving this growth include technological innovation, regulatory changes, and evolving customer demands in {target_market}.",
                "score": 0.9,
                "search_query": f"{industry} industry outlook {year}",
                "search_type": "demo_market_analysis"
            },
            {
                "title": f"{target_market} {industry} Market Size and Trends",
                "url": f"https://marketdata.com/{target_market.lower().replace(' ', '-')}-{industry.lower()}-trends",
                "content": f"Market size analysis for {industry} in {target_market} reveals strong consumer adoption and enterprise investment. Emerging technologies and changing business models are reshaping the competitive landscape.",
                "score": 0.88,
                "search_query": f"{industry} market size {target_market}",
                "search_type": "demo_market_analysis"
            },
            {
                "title": f"Competitive Landscape: {industry} Industry {year}",
                "url": f"https://competitiveanalysis.com/{industry.lower()}-landscape",
                "content": f"Analysis of competitive dynamics in the {industry} sector. Market concentration, key players, and strategic positioning across {target_market}. Includes market share data and competitive threats.",
                "score": 0.85,
                "search_query": f"{industry} competitive landscape",
                "search_type": "demo_market_analysis"
            }
        ]
        
        logger.info(f"Generated {len(demo_results)} demo market analysis records for {industry} industry")
        
        # Simulate network delay
        await asyncio.sleep(0.3)
        
        return demo_results
    
    async def _get_demo_company_details(self, company_name: str) -> List[Dict[str, Any]]:
        """Generate demo company details when real API is unavailable"""
        
        demo_results = [
            {
                "title": f"{company_name} - Company Overview",
                "url": f"https://{company_name.lower().replace(' ', '')}.com/about",
                "content": f"{company_name} is a leading company providing innovative solutions. Founded in 2010, the company has grown to serve millions of customers worldwide with a focus on quality and innovation.",
                "score": 0.95,
                "search_query": f"{company_name} company profile",
                "search_type": "demo_company_details"
            },
            {
                "title": f"{company_name} Products and Services",
                "url": f"https://{company_name.lower().replace(' ', '')}.com/products",
                "content": f"{company_name} offers a comprehensive suite of products and services designed to meet diverse customer needs. Their flagship products include enterprise solutions, cloud services, and professional consulting.",
                "score": 0.9,
                "search_query": f"{company_name} products services",
                "search_type": "demo_company_details"
            },
            {
                "title": f"{company_name} Leadership Team",
                "url": f"https://{company_name.lower().replace(' ', '')}.com/leadership",
                "content": f"The leadership team at {company_name} brings decades of industry experience. CEO Jane Doe has led the company through significant growth, while CTO John Smith drives innovation.",
                "score": 0.85,
                "search_query": f"{company_name} leadership team",
                "search_type": "demo_company_details"
            },
            {
                "title": f"{company_name} Recent News and Updates",
                "url": f"https://news.example.com/{company_name.lower()}-updates",
                "content": f"Recent developments at {company_name}: Q4 revenue up 25%, new product launches, strategic partnerships announced, and expansion into new markets.",
                "score": 0.88,
                "search_query": f"{company_name} recent news",
                "search_type": "demo_company_details"
            }
        ]
        
        logger.info(f"Generated {len(demo_results)} demo company detail records for {company_name}")
        await asyncio.sleep(0.3)
        
        return demo_results
    
    async def _get_demo_custom_search(self, query: str, search_type: str) -> List[Dict[str, Any]]:
        """Generate demo search results for custom queries"""
        
        demo_results = [
            {
                "title": f"Search Results for: {query[:50]}",
                "url": f"https://search.example.com/results?q={query.replace(' ', '+')}",
                "content": f"Comprehensive search results for your query. This demo result provides relevant information related to: {query}. The content includes detailed analysis and insights.",
                "score": 0.9,
                "search_query": query,
                "search_type": f"demo_{search_type}"
            },
            {
                "title": f"Industry Analysis: {query[:40]}",
                "url": f"https://industry.example.com/analysis",
                "content": f"In-depth analysis related to your search query. Market trends, competitive landscape, and strategic insights for: {query}",
                "score": 0.85,
                "search_query": query,
                "search_type": f"demo_{search_type}"
            },
            {
                "title": f"Expert Insights on {query[:35]}",
                "url": f"https://insights.example.com/expert-view",
                "content": f"Expert perspectives and professional analysis on the topic. Leading industry experts share their views on: {query}",
                "score": 0.8,
                "search_query": query,
                "search_type": f"demo_{search_type}"
            }
        ]
        
        logger.info(f"Generated {len(demo_results)} demo custom search results for query: {query[:50]}")
        await asyncio.sleep(0.2)
        
        return demo_results