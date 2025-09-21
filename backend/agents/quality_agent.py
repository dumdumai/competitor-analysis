import asyncio
from typing import Dict, Any, List
from loguru import logger
from models.agent_state import AgentState
from models.analysis import CompetitorData
from services.redis_service import RedisService


class QualityAgent:
    """
    Unified quality assurance and data validation agent.
    Combines data enrichment, quality scoring, and validation functionality.
    """
    
    def __init__(self, redis_service: RedisService):
        self.name = "quality_agent"
        self.redis_service = redis_service
        self.min_quality_threshold = 0.3  # Lowered threshold to be more permissive
        self.quality_weights = {
            "data_completeness": 0.3,
            "data_accuracy": 0.25,
            "relevance_score": 0.25,
            "recency_score": 0.2
        }
    
    async def process(self, state: AgentState) -> AgentState:
        """Execute comprehensive quality assurance and data enrichment"""
        try:
            logger.info(f"🔍 Starting quality assurance for {len(state.discovered_competitors)} competitors")
            
            # Update progress
            await self._update_progress(state, "quality", 5, "Initializing quality assessment")
            
            # Stage 1: Convert raw search data to structured competitor data
            await self._update_progress(state, "quality", 20, "Processing competitor data")
            competitor_data_list = await self._process_competitor_data(state)
            
            # Stage 2: Quality scoring and validation
            await self._update_progress(state, "quality", 50, "Calculating quality scores")
            scored_competitors = await self._score_and_validate_competitors(competitor_data_list, state)
            
            # Stage 3: Data enrichment and gap filling
            await self._update_progress(state, "quality", 80, "Enriching competitor profiles")
            enriched_competitors = await self._enrich_competitor_data(scored_competitors, state)
            
            # Update state with processed data
            state.competitor_data = enriched_competitors
            
            # Calculate final quality metrics
            high_quality_count = len([c for c in enriched_competitors if state.quality_scores.get(c.name, 0) >= self.min_quality_threshold])
            average_quality = sum(state.quality_scores.values()) / len(state.quality_scores) if state.quality_scores else 0
            
            # Stage 4: Generate quality issues and potential retries
            await self._update_progress(state, "quality", 90, "Identifying quality issues")
            await self._identify_quality_issues(state, enriched_competitors, high_quality_count, average_quality)
            
            # Update metadata
            state.metadata.update({
                "total_competitors_processed": len(enriched_competitors),
                "high_quality_competitors": high_quality_count,
                "average_quality_score": round(average_quality, 2),
                "quality_threshold": self.min_quality_threshold,
                "quality_assessment_completed": True,
                "quality_issues_identified": len(state.retry_context.quality_feedback)
            })
            
            # Complete the stage
            state.complete_stage("quality")
            await self._update_progress(state, "quality", 100, f"Quality assessment completed: {high_quality_count}/{len(enriched_competitors)} high-quality competitors")
            
            # Log quality assessment results
            if state.retry_context.quality_feedback:
                logger.warning(f"⚠️ Quality assessment found {len(state.retry_context.quality_feedback)} issues that may require retries")
            else:
                logger.info(f"✅ Quality assessment completed: {high_quality_count}/{len(enriched_competitors)} competitors meet quality threshold")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in quality agent: {e}")
            state.add_error(f"Quality assessment failed: {str(e)}")
            return state
    
    async def _process_competitor_data(self, state: AgentState) -> List[CompetitorData]:
        """Convert raw search data to structured CompetitorData objects"""
        competitor_data_list = []
        
        # Get search data for each discovered competitor
        for competitor_name in state.discovered_competitors:
            try:
                # Find relevant search results for this competitor
                competitor_results = self._extract_competitor_results(competitor_name, state.search_results)
                
                # Create CompetitorData object
                competitor_data = self._create_competitor_data(competitor_name, competitor_results)
                competitor_data_list.append(competitor_data)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to process data for {competitor_name}: {e}")
                # Create minimal competitor data
                competitor_data = CompetitorData(
                    name=competitor_name,
                    website="",
                    description="Data processing failed",
                    business_model="Unknown",
                    target_market=state.analysis_context.target_market,
                    founding_year=None,
                    headquarters="Unknown",
                    employee_count="Unknown",
                    key_products=[],
                    pricing_strategy="Unknown",
                    market_position="Unknown",
                    strengths=[],
                    weaknesses=["Limited data available"],
                    technology_stack=[],
                    partnerships=[],
                    competitive_advantages=[],
                    recent_news=[]
                )
                competitor_data_list.append(competitor_data)
        
        return competitor_data_list
    
    def _extract_competitor_results(self, competitor_name: str, search_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Extract search results relevant to a specific competitor"""
        relevant_results = []
        competitor_lower = competitor_name.lower()
        
        # Check all search result categories
        for category, results in search_results.items():
            for result in results:
                title = result.get('title', '').lower()
                content = result.get('content', '').lower()
                
                # Check if this result is about the competitor
                if competitor_lower in title or competitor_lower in content:
                    result['category'] = category
                    relevant_results.append(result)
        
        return relevant_results
    
    def _create_competitor_data(self, competitor_name: str, search_results: List[Dict[str, Any]]) -> CompetitorData:
        """Create CompetitorData object from search results"""
        # Extract basic information
        website = self._extract_website(search_results)
        description = self._extract_description(search_results)
        business_model = self._extract_business_model(search_results)
        
        # Extract structured data
        key_products = self._extract_key_products(search_results)
        strengths = self._extract_strengths(search_results)
        weaknesses = self._extract_weaknesses(search_results)
        
        return CompetitorData(
            name=competitor_name,
            website=website,
            description=description,
            business_model=business_model,
            target_market="Unknown",  # Will be enriched later
            founding_year=self._extract_founding_year(search_results),
            headquarters=self._extract_headquarters(search_results),
            employee_count=self._extract_employee_count(search_results),
            key_products=key_products,
            pricing_strategy=self._extract_pricing_strategy(search_results),
            market_position=self._extract_market_position(search_results),
            strengths=strengths,
            weaknesses=weaknesses,
            technology_stack=self._extract_technology_stack(search_results),
            partnerships=self._extract_partnerships(search_results),
            competitive_advantages=self._extract_competitive_advantages(search_results),
            recent_news=self._extract_recent_news(search_results)
        )
    
    async def _score_and_validate_competitors(self, competitors: List[CompetitorData], state: AgentState) -> List[CompetitorData]:
        """Calculate quality scores for each competitor"""
        scored_competitors = []
        
        for competitor in competitors:
            # Calculate individual quality metrics
            completeness_score = self._calculate_completeness_score(competitor)
            accuracy_score = self._calculate_accuracy_score(competitor, state)
            relevance_score = self._calculate_relevance_score(competitor, state)
            recency_score = self._calculate_recency_score(competitor)
            
            # Calculate weighted overall score
            overall_score = (
                completeness_score * self.quality_weights["data_completeness"] +
                accuracy_score * self.quality_weights["data_accuracy"] +
                relevance_score * self.quality_weights["relevance_score"] +
                recency_score * self.quality_weights["recency_score"]
            )
            
            # Store quality score
            state.set_quality_score(competitor.name, overall_score)
            
            # Only include if meets minimum threshold
            if overall_score >= self.min_quality_threshold:
                scored_competitors.append(competitor)
            else:
                logger.warning(f"⚠️ {competitor.name} excluded - quality score {overall_score:.2f} below threshold {self.min_quality_threshold}")
        
        return scored_competitors
    
    async def _enrich_competitor_data(self, competitors: List[CompetitorData], state: AgentState) -> List[CompetitorData]:
        """Enrich competitor data with additional context"""
        enriched_competitors = []
        
        for competitor in competitors:
            # Add industry context
            if not competitor.target_market or competitor.target_market == "Unknown":
                competitor.target_market = state.analysis_context.target_market
            
            # Infer business model if missing
            if not competitor.business_model or competitor.business_model == "Unknown":
                competitor.business_model = self._infer_business_model(competitor)
            
            # Add competitive positioning context
            if not competitor.market_position or competitor.market_position == "Unknown":
                competitor.market_position = self._infer_market_position(competitor, state)
            
            enriched_competitors.append(competitor)
        
        return enriched_competitors
    
    # Data extraction helper methods
    def _extract_website(self, results: List[Dict[str, Any]]) -> str:
        """Extract website URL from search results"""
        for result in results:
            url = result.get('url', '')
            if url and not any(domain in url for domain in ['linkedin.com', 'facebook.com', 'twitter.com', 'crunchbase.com']):
                return url
        return ""
    
    def _extract_description(self, results: List[Dict[str, Any]]) -> str:
        """Extract company description from search results"""
        descriptions = []
        for result in results:
            content = result.get('content', '')
            if len(content) > 50:
                descriptions.append(content[:200])
        
        return descriptions[0] if descriptions else "No description available"
    
    def _extract_business_model(self, results: List[Dict[str, Any]]) -> str:
        """Extract business model information"""
        for result in results:
            content = result.get('content', '').lower()
            if any(term in content for term in ['saas', 'subscription', 'b2b', 'b2c', 'marketplace', 'freemium']):
                if 'saas' in content or 'subscription' in content:
                    return "SaaS/Subscription"
                elif 'marketplace' in content:
                    return "Marketplace"
                elif 'b2b' in content:
                    return "B2B"
                elif 'b2c' in content:
                    return "B2C"
        return "Unknown"
    
    def _extract_key_products(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract key products/services"""
        products = []
        for result in results:
            title = result.get('title', '')
            content = result.get('content', '')
            # Simple keyword extraction - could be enhanced with NLP
            if 'product' in content.lower() or 'service' in content.lower():
                words = content.split()
                for i, word in enumerate(words):
                    if word.lower() in ['product', 'service', 'solution']:
                        if i > 0:
                            products.append(words[i-1].strip(',.:'))
        
        return list(set(products[:5]))  # Return up to 5 unique products
    
    def _extract_strengths(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract competitive strengths"""
        strengths = []
        positive_keywords = ['leading', 'innovative', 'award', 'top', 'best', 'strong', 'growth', 'successful']
        
        for result in results:
            content = result.get('content', '').lower()
            for keyword in positive_keywords:
                if keyword in content:
                    strengths.append(f"Market recognition ({keyword})")
                    break
        
        return list(set(strengths[:3]))  # Return up to 3 unique strengths
    
    def _extract_weaknesses(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract potential weaknesses or challenges"""
        weaknesses = []
        negative_keywords = ['challenge', 'issue', 'problem', 'criticism', 'controversy', 'decline']
        
        for result in results:
            content = result.get('content', '').lower()
            for keyword in negative_keywords:
                if keyword in content:
                    weaknesses.append(f"Potential challenges identified")
                    break
        
        return list(set(weaknesses[:2]))  # Return up to 2 unique weaknesses
    
    # Additional extraction methods with basic implementations
    def _extract_founding_year(self, results: List[Dict[str, Any]]) -> int:
        """Extract founding year"""
        import re
        for result in results:
            content = result.get('content', '')
            years = re.findall(r'\b(19|20)\d{2}\b', content)
            if years:
                return int(years[0])
        return None
    
    def _extract_headquarters(self, results: List[Dict[str, Any]]) -> str:
        """Extract headquarters location"""
        locations = ['San Francisco', 'New York', 'London', 'Seattle', 'Austin', 'Boston']
        for result in results:
            content = result.get('content', '')
            for location in locations:
                if location in content:
                    return location
        return "Unknown"
    
    def _extract_employee_count(self, results: List[Dict[str, Any]]) -> str:
        """Extract employee count"""
        import re
        for result in results:
            content = result.get('content', '')
            # Look for employee count patterns
            employee_pattern = re.search(r'(\d+[\+\-\s]*(?:thousand|k|employees|staff|people))', content.lower())
            if employee_pattern:
                return employee_pattern.group(1)
        return "Unknown"
    
    def _extract_pricing_strategy(self, results: List[Dict[str, Any]]) -> str:
        """Extract pricing strategy"""
        for result in results:
            content = result.get('content', '').lower()
            if any(term in content for term in ['free', 'freemium', 'subscription', 'pricing', 'cost']):
                if 'freemium' in content:
                    return "Freemium"
                elif 'subscription' in content:
                    return "Subscription-based"
                elif 'free' in content:
                    return "Free/Open Source"
        return "Unknown"
    
    def _extract_market_position(self, results: List[Dict[str, Any]]) -> str:
        """Extract market position"""
        position_keywords = {
            'leader': 'Market Leader',
            'dominant': 'Market Leader',
            'challenger': 'Market Challenger',
            'startup': 'Emerging Player',
            'niche': 'Niche Player'
        }
        
        for result in results:
            content = result.get('content', '').lower()
            for keyword, position in position_keywords.items():
                if keyword in content:
                    return position
        return "Unknown"
    
    def _extract_technology_stack(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract technology stack information"""
        tech_keywords = ['python', 'javascript', 'react', 'aws', 'azure', 'kubernetes', 'docker', 'api']
        tech_stack = []
        
        for result in results:
            content = result.get('content', '').lower()
            for tech in tech_keywords:
                if tech in content:
                    tech_stack.append(tech.capitalize())
        
        return list(set(tech_stack[:5]))
    
    def _extract_partnerships(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract partnership information"""
        partnerships = []
        partner_keywords = ['partnership', 'partner', 'collaboration', 'integration']
        
        for result in results:
            content = result.get('content', '')
            title = result.get('title', '')
            if any(keyword in content.lower() for keyword in partner_keywords):
                # Simple extraction - could be enhanced
                partnerships.append(f"Strategic partnerships mentioned")
        
        return list(set(partnerships[:3]))
    
    def _extract_competitive_advantages(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract competitive advantages"""
        advantages = []
        advantage_keywords = ['unique', 'proprietary', 'patented', 'exclusive', 'first', 'only']
        
        for result in results:
            content = result.get('content', '').lower()
            for keyword in advantage_keywords:
                if keyword in content:
                    advantages.append(f"Market differentiation ({keyword})")
                    break
        
        return list(set(advantages[:3]))
    
    def _extract_recent_news(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract recent news items"""
        news_items = []
        
        for result in results:
            if result.get('category') in ['news', 'recent_updates']:
                news_item = {
                    "title": result.get('title', '')[:100],
                    "date": "Recent",
                    "summary": result.get('content', '')[:200]
                }
                news_items.append(news_item)
        
        return news_items[:3]  # Return up to 3 recent news items
    
    # Quality scoring methods
    def _calculate_completeness_score(self, competitor: CompetitorData) -> float:
        """Calculate data completeness score"""
        fields_to_check = [
            competitor.name, competitor.website, competitor.description,
            competitor.business_model, competitor.target_market
        ]
        
        filled_fields = sum(1 for field in fields_to_check if field and field != "Unknown" and field != "")
        completeness_score = filled_fields / len(fields_to_check)
        
        # Bonus for having additional data
        if competitor.key_products:
            completeness_score += 0.1
        if competitor.strengths:
            completeness_score += 0.1
        if competitor.recent_news:
            completeness_score += 0.1
        
        return min(completeness_score, 1.0)
    
    def _calculate_accuracy_score(self, competitor: CompetitorData, state: AgentState) -> float:
        """Calculate data accuracy score (basic implementation)"""
        accuracy_score = 0.8  # Base accuracy assumption
        
        # Penalize if description is too short or generic
        if len(competitor.description) < 50:
            accuracy_score -= 0.2
        
        # Bonus for having website
        if competitor.website:
            accuracy_score += 0.1
        
        # Bonus for having specific business model
        if competitor.business_model not in ["Unknown", ""]:
            accuracy_score += 0.1
        
        return min(accuracy_score, 1.0)
    
    def _calculate_relevance_score(self, competitor: CompetitorData, state: AgentState) -> float:
        """Calculate relevance score based on analysis context"""
        context = state.analysis_context
        relevance_score = 0.5  # Base relevance
        
        # Check industry alignment
        if context.industry.lower() in competitor.description.lower():
            relevance_score += 0.2
        
        # Check target market alignment
        if context.target_market.lower() in competitor.target_market.lower():
            relevance_score += 0.2
        
        # Check business model alignment
        if context.business_model.lower() in competitor.business_model.lower():
            relevance_score += 0.1
        
        return min(relevance_score, 1.0)
    
    def _calculate_recency_score(self, competitor: CompetitorData) -> float:
        """Calculate recency score based on data freshness"""
        recency_score = 0.7  # Base assumption for recent data
        
        # Bonus for recent news
        if competitor.recent_news:
            recency_score += 0.2
        
        # Bonus for founding year information
        if competitor.founding_year:
            recency_score += 0.1
        
        return min(recency_score, 1.0)
    
    # Data enrichment methods
    def _infer_business_model(self, competitor: CompetitorData) -> str:
        """Infer business model from available data"""
        description = competitor.description.lower()
        
        if any(term in description for term in ['software', 'platform', 'cloud', 'api']):
            return "SaaS/Technology"
        elif any(term in description for term in ['marketplace', 'connect', 'platform']):
            return "Marketplace/Platform"
        elif any(term in description for term in ['consulting', 'services', 'advisory']):
            return "Professional Services"
        else:
            return "Traditional Business"
    
    def _infer_market_position(self, competitor: CompetitorData, state: AgentState) -> str:
        """Infer market position from available data"""
        description = competitor.description.lower()
        
        if any(term in description for term in ['leading', 'largest', 'dominant', '#1']):
            return "Market Leader"
        elif any(term in description for term in ['startup', 'founded', 'new', 'emerging']):
            return "Emerging Player"
        elif any(term in description for term in ['specialist', 'focused', 'niche']):
            return "Niche Player"
        else:
            return "Market Participant"
    
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
    
    async def _identify_quality_issues(self, state: AgentState, competitors: List[CompetitorData], 
                                     high_quality_count: int, average_quality: float):
        """Identify quality issues that may require agent retries"""
        from models.agent_state import QualityIssue
        
        # Check if we have enough competitors
        min_expected_competitors = max(3, state.analysis_context.max_competitors // 2)
        if len(competitors) < min_expected_competitors:
            issue = QualityIssue(
                issue_type="insufficient_competitors",
                severity="high",
                description=f"Only found {len(competitors)} competitors, expected at least {min_expected_competitors}",
                affected_competitors=[],
                suggested_action="Expand search scope and use broader search terms",
                retry_agent="search",
                additional_params={"target_count": min_expected_competitors + 2}
            )
            state.add_quality_issue(issue)
            logger.warning(f"🔍 Quality issue: Insufficient competitors found ({len(competitors)} < {min_expected_competitors})")
        
        # Check data completeness
        incomplete_competitors = []
        for competitor in competitors:
            completeness_score = self._calculate_completeness_score(competitor)
            if completeness_score < 0.5:  # Less than 50% data completeness
                incomplete_competitors.append(competitor.name)
        
        if len(incomplete_competitors) > len(competitors) * 0.3:  # More than 30% incomplete
            issue = QualityIssue(
                issue_type="data_completeness",
                severity="high",
                description=f"Data completeness issues for {len(incomplete_competitors)} competitors",
                affected_competitors=incomplete_competitors,
                suggested_action="Search for additional data sources and enhance data collection",
                retry_agent="search",
                additional_params={
                    "search_terms": ["company profile", "business details", "company information"],
                    "incomplete_competitors": incomplete_competitors
                }
            )
            state.add_quality_issue(issue)
            logger.warning(f"📊 Quality issue: Data completeness problems for {len(incomplete_competitors)} competitors")
        
        # Check overall quality average
        quality_threshold_for_retry = 0.6
        if average_quality < quality_threshold_for_retry:
            issue = QualityIssue(
                issue_type="overall_quality_low",
                severity="medium",
                description=f"Average quality score {average_quality:.2f} is below threshold {quality_threshold_for_retry}",
                affected_competitors=[c.name for c in competitors],
                suggested_action="Enhance data collection and validation processes",
                retry_agent="search",
                additional_params={"quality_threshold": quality_threshold_for_retry}
            )
            state.add_quality_issue(issue)
            logger.warning(f"📉 Quality issue: Overall quality ({average_quality:.2f}) below threshold")
        
        # Check relevance issues
        low_relevance_competitors = []
        for competitor in competitors:
            relevance_score = self._calculate_relevance_score(competitor, state)
            if relevance_score < 0.4:  # Less than 40% relevance
                low_relevance_competitors.append(competitor.name)
        
        if len(low_relevance_competitors) > 0:
            issue = QualityIssue(
                issue_type="relevance_low",
                severity="medium",
                description=f"Low relevance scores for {len(low_relevance_competitors)} competitors",
                affected_competitors=low_relevance_competitors,
                suggested_action="Focus search on industry-specific terms and target market",
                retry_agent="search",
                additional_params={
                    "focus_keywords": [state.analysis_context.industry, state.analysis_context.target_market],
                    "low_relevance_competitors": low_relevance_competitors
                }
            )
            state.add_quality_issue(issue)
            logger.warning(f"🎯 Quality issue: Low relevance for {len(low_relevance_competitors)} competitors")
        
        # Check analysis quality (if analysis has been completed)
        if hasattr(state, 'market_insights') and state.market_insights:
            if self._is_analysis_shallow(state.market_insights):
                issue = QualityIssue(
                    issue_type="analysis_depth",
                    severity="high",
                    description="Market analysis appears shallow or incomplete",
                    affected_competitors=[],
                    suggested_action="Enhance analysis depth with more detailed prompts",
                    retry_agent="analysis",
                    additional_params={"analysis_type": "market"}
                )
                state.add_quality_issue(issue)
                logger.warning("📊 Quality issue: Shallow market analysis detected")
        
        if hasattr(state, 'competitive_analysis') and state.competitive_analysis:
            if self._is_analysis_shallow(state.competitive_analysis):
                issue = QualityIssue(
                    issue_type="competitive_positioning",
                    severity="high",
                    description="Competitive analysis appears shallow or incomplete",
                    affected_competitors=[],
                    suggested_action="Enhance competitive analysis with deeper insights",
                    retry_agent="analysis",
                    additional_params={"analysis_type": "competitive"}
                )
                state.add_quality_issue(issue)
                logger.warning("🏆 Quality issue: Shallow competitive analysis detected")
        
        # Check recommendations quality
        if hasattr(state, 'recommendations') and state.recommendations:
            if len(state.recommendations) < 3 or any(len(rec) < 50 for rec in state.recommendations):
                issue = QualityIssue(
                    issue_type="recommendations_quality",
                    severity="medium",
                    description="Recommendations are insufficient or too brief",
                    affected_competitors=[],
                    suggested_action="Generate more detailed and actionable recommendations",
                    retry_agent="analysis",
                    additional_params={"min_recommendations": 5, "min_length": 100}
                )
                state.add_quality_issue(issue)
                logger.warning("💡 Quality issue: Poor recommendations quality")
    
    def _is_analysis_shallow(self, analysis: Dict[str, Any]) -> bool:
        """Check if analysis appears shallow"""
        if not analysis or "error" in analysis:
            return True
        
        # Check for generic or minimal content
        if isinstance(analysis, dict):
            content_strings = []
            for value in analysis.values():
                if isinstance(value, str):
                    content_strings.append(value)
                elif isinstance(value, list):
                    content_strings.extend([str(item) for item in value])
            
            # Check total content length
            total_content = " ".join(content_strings)
            if len(total_content) < 200:  # Less than 200 characters
                return True
            
            # Check for generic phrases
            generic_phrases = ["analysis requires", "not available", "basic", "unknown", "N/A"]
            if any(phrase in total_content.lower() for phrase in generic_phrases):
                return True
        
        return False