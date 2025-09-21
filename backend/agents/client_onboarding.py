from typing import Dict, Any, List
from loguru import logger
from models.agent_state import AgentState, AnalysisContext
from models.analysis import AnalysisRequest


class ClientOnboardingAgent:
    """Agent responsible for processing client requirements and setting up analysis context"""
    
    def __init__(self):
        self.name = "client_onboarding"
    
    async def process(self, state: AgentState) -> AgentState:
        """Process client onboarding and setup analysis context"""
        try:
            logger.info(f"Starting client onboarding for {state.analysis_context.client_company}")
            
            # Update progress
            state.update_progress("client_onboarding", 10)
            
            # Validate required information
            validation_result = self._validate_client_requirements(state.analysis_context)
            
            if not validation_result["valid"]:
                state.add_error(f"Client requirements validation failed: {validation_result['errors']}")
                state.status = "failed"
                return state
            
            # Generate search keywords
            search_keywords = self._generate_search_keywords(state.analysis_context)
            state.analysis_context.search_keywords = search_keywords
            
            # Set data quality requirements
            quality_requirements = self._define_quality_requirements(state.analysis_context)
            state.analysis_context.quality_requirements = quality_requirements
            
            # Set data sources preferences
            data_sources = self._define_data_sources(state.analysis_context)
            state.analysis_context.data_sources = data_sources
            
            # Update metadata
            state.metadata.update({
                "onboarding_completed": True,
                "search_keywords_count": len(search_keywords),
                "quality_requirements_set": True
            })
            
            # Complete the stage
            state.complete_stage("client_onboarding")
            state.update_progress("client_onboarding", 100)
            
            logger.info(f"Client onboarding completed for {state.analysis_context.client_company}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in client onboarding: {e}")
            state.add_error(f"Client onboarding failed: {str(e)}")
            state.status = "failed"
            return state
    
    def _validate_client_requirements(self, context: AnalysisContext) -> Dict[str, Any]:
        """Validate that all required client information is provided"""
        errors = []
        
        if not context.client_company or context.client_company.strip() == "":
            errors.append("Client company name is required")
        
        if not context.industry or context.industry.strip() == "":
            errors.append("Industry is required")
        
        if not context.target_market or context.target_market.strip() == "":
            errors.append("Target market is required")
        
        if not context.business_model or context.business_model.strip() == "":
            errors.append("Business model is required")
        
        if context.max_competitors <= 0 or context.max_competitors > 50:
            errors.append("Maximum competitors must be between 1 and 50")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _generate_search_keywords(self, context: AnalysisContext) -> List[str]:
        """Generate comprehensive search keywords based on client context"""
        keywords = []
        
        # Base company and industry terms
        keywords.extend([
            context.client_company,
            context.industry,
            context.target_market,
            context.business_model
        ])
        
        # Industry-specific keywords
        industry_lower = context.industry.lower()
        
        if "saas" in industry_lower or "software" in industry_lower:
            keywords.extend([
                "software companies", "SaaS platforms", "cloud software",
                "enterprise software", "business software"
            ])
        elif "fintech" in industry_lower or "financial" in industry_lower:
            keywords.extend([
                "fintech companies", "financial services", "payment platforms",
                "banking software", "financial technology"
            ])
        elif "ecommerce" in industry_lower or "e-commerce" in industry_lower:
            keywords.extend([
                "ecommerce platforms", "online retail", "marketplace",
                "digital commerce", "retail technology"
            ])
        elif "healthcare" in industry_lower or "health" in industry_lower:
            keywords.extend([
                "healthcare companies", "health tech", "medical software",
                "digital health", "telemedicine"
            ])
        elif "education" in industry_lower or "edtech" in industry_lower:
            keywords.extend([
                "edtech companies", "education technology", "online learning",
                "educational software", "learning platforms"
            ])
        
        # Business model specific keywords
        business_model_lower = context.business_model.lower()
        
        if "b2b" in business_model_lower:
            keywords.extend(["B2B companies", "enterprise solutions", "business services"])
        elif "b2c" in business_model_lower:
            keywords.extend(["B2C companies", "consumer products", "retail"])
        elif "marketplace" in business_model_lower:
            keywords.extend(["marketplace platforms", "two-sided markets", "platform business"])
        elif "subscription" in business_model_lower:
            keywords.extend(["subscription services", "recurring revenue", "membership"])
        
        # Target market keywords
        if context.target_market:
            target_market_lower = context.target_market.lower()
            keywords.append(f"{context.industry} {context.target_market}")
            
            if any(geo in target_market_lower for geo in ["us", "usa", "america", "north america"]):
                keywords.extend([f"US {context.industry}", f"American {context.industry}"])
            elif any(geo in target_market_lower for geo in ["europe", "eu", "european"]):
                keywords.extend([f"European {context.industry}", f"EU {context.industry}"])
            elif any(geo in target_market_lower for geo in ["asia", "asian"]):
                keywords.extend([f"Asian {context.industry}", f"Asia {context.industry}"])
        
        # Remove duplicates and empty strings
        keywords = list(set([k.strip() for k in keywords if k and k.strip()]))
        
        return keywords[:20]  # Limit to top 20 keywords
    
    def _define_quality_requirements(self, context: AnalysisContext) -> Dict[str, Any]:
        """Define data quality requirements based on client needs"""
        return {
            "minimum_data_points": 5,  # Minimum data points per competitor
            "required_fields": [
                "name", "description", "business_model", "target_market"
            ],
            "preferred_fields": [
                "website", "founding_year", "headquarters", "employee_count",
                "key_products", "pricing_strategy", "strengths", "weaknesses"
            ],
            "data_freshness_days": 30,  # Data should be no older than 30 days
            "source_diversity": 3,  # Minimum 3 different sources per competitor
            "confidence_threshold": 0.7  # Minimum confidence score
        }
    
    def _define_data_sources(self, context: AnalysisContext) -> List[str]:
        """Define preferred data sources based on industry and requirements"""
        sources = [
            "company_websites",
            "news_articles", 
            "industry_reports",
            "social_media",
            "press_releases"
        ]
        
        # Industry-specific sources
        industry_lower = context.industry.lower()
        
        if "tech" in industry_lower or "software" in industry_lower:
            sources.extend([
                "crunchbase", "techcrunch", "github", "product_hunt"
            ])
        elif "finance" in industry_lower:
            sources.extend([
                "bloomberg", "reuters", "financial_reports", "sec_filings"
            ])
        elif "retail" in industry_lower or "ecommerce" in industry_lower:
            sources.extend([
                "retail_reports", "ecommerce_news", "marketplace_data"
            ])
        
        return sources