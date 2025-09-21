import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from loguru import logger


class LLMService:
    """Service for OpenAI/Azure OpenAI LLM interactions"""
    
    def __init__(self):
        # Check if Azure OpenAI credentials are available
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        
        if azure_endpoint and azure_api_key and azure_deployment:
            # Use Azure OpenAI
            try:
                # Try different initialization approaches for Azure OpenAI compatibility
                import httpx
                
                # Create Azure OpenAI base URL with deployment path
                api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
                base_url = f"{azure_endpoint.rstrip('/')}/openai/deployments/{azure_deployment}"
                
                self.client = AsyncOpenAI(
                    api_key=azure_api_key,
                    base_url=base_url,
                    default_query={"api-version": api_version},
                    http_client=httpx.AsyncClient()
                )
                # For Azure, we use the deployment name as model, but in the URL path
                self.model = azure_deployment
                self.is_azure = True
                logger.info(f"Initialized Azure OpenAI client with deployment: {azure_deployment}")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {e}")
                # Fall back to basic OpenAI initialization without Azure-specific params
                try:
                    self.client = AsyncOpenAI(api_key=azure_api_key)
                    self.model = "gpt-4"  # Default model
                    self.is_azure = False
                    logger.warning("Falling back to basic OpenAI client configuration")
                except Exception as e2:
                    logger.error(f"Failed to initialize any OpenAI client: {e2}")
                    self.client = None
                    self.is_azure = False
        else:
            # Fall back to regular OpenAI
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.is_azure = False
            
            if not self.api_key:
                logger.warning("Neither Azure OpenAI nor OpenAI API key provided - LLM functionality will be limited")
                self.client = None
            else:
                try:
                    self.client = AsyncOpenAI(api_key=self.api_key)
                    logger.info("Initialized regular OpenAI client")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
                    self.client = None
            
            self.model = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
        
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4000"))
    
    async def extract_competitor_info(self, 
                                    company_name: str, 
                                    search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract structured competitor information from search results"""
        try:
            # Prepare content from search results
            content_parts = []
            for result in search_results:
                content_parts.append(f"URL: {result.get('url', '')}")
                content_parts.append(f"Title: {result.get('title', '')}")
                content_parts.append(f"Content: {result.get('content', '')[:1000]}...")  # Limit content length
                content_parts.append("---")
            
            content = "\n".join(content_parts)
            
            system_prompt = """You are an expert business analyst. Extract structured information about the company from the provided search results. 
            Return a JSON object with the following structure:
            {
                "name": "Company Name",
                "website": "company website URL",
                "description": "company description",
                "business_model": "business model description",
                "target_market": "target market",
                "founding_year": year or null,
                "headquarters": "location or null",
                "employee_count": "employee range or null",
                "funding_info": {
                    "total_funding": "amount or null",
                    "last_round": "round type or null",
                    "investors": ["investor1", "investor2"] or []
                },
                "key_products": ["product1", "product2"],
                "pricing_strategy": "pricing model or null",
                "market_position": "market position description",
                "strengths": ["strength1", "strength2"],
                "weaknesses": ["weakness1", "weakness2"],
                "recent_news": [
                    {"title": "news title", "date": "date", "summary": "summary"}
                ],
                "technology_stack": ["tech1", "tech2"],
                "partnerships": ["partner1", "partner2"],
                "competitive_advantages": ["advantage1", "advantage2"],
                "market_share": percentage or null,
                "growth_trajectory": "growth description"
            }
            
            Extract only factual information. If information is not available, use null or empty arrays.
            Focus on accuracy over completeness."""
            
            user_prompt = f"""Extract information about {company_name} from the following search results:

{content}

Company to analyze: {company_name}

Please return a JSON object with the structured information."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content.strip()
            
            # Clean up the response if it has markdown formatting
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error extracting competitor info for {company_name}: {e}")
            return {
                "name": company_name,
                "description": "Information extraction failed",
                "error": str(e)
            }
    
    async def analyze_market_landscape(self, 
                                     industry: str,
                                     competitors: List[Dict[str, Any]],
                                     search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the overall market landscape"""
        try:
            # Prepare competitor summary
            competitor_summary = []
            for comp in competitors:
                competitor_summary.append(f"- {comp.get('name', 'Unknown')}: {comp.get('description', 'No description')}")
            
            competitors_text = "\n".join(competitor_summary)
            
            # Prepare market content
            market_content = []
            for result in search_results:
                if result.get('search_type') == 'market_analysis':
                    market_content.append(f"Title: {result.get('title', '')}")
                    market_content.append(f"Content: {result.get('content', '')[:800]}...")
                    market_content.append("---")
            
            market_text = "\n".join(market_content)
            
            system_prompt = """You are a senior market research analyst. Analyze the market landscape based on the competitor data and market research provided.
            
            Return a JSON object with this structure:
            {
                "market_size": {
                    "current_size": "market size description",
                    "growth_rate": "growth rate or null",
                    "forecast": "market forecast"
                },
                "key_trends": ["trend1", "trend2", "trend3"],
                "market_segments": [
                    {"name": "segment name", "description": "description", "size": "relative size"}
                ],
                "competitive_intensity": "high/medium/low",
                "barriers_to_entry": ["barrier1", "barrier2"],
                "key_success_factors": ["factor1", "factor2"],
                "emerging_opportunities": ["opportunity1", "opportunity2"],
                "market_threats": ["threat1", "threat2"],
                "technology_disruptions": ["disruption1", "disruption2"],
                "regulatory_factors": ["factor1", "factor2"]
            }
            
            Provide strategic insights based on the data."""
            
            user_prompt = f"""Analyze the {industry} market landscape based on:

COMPETITORS:
{competitors_text}

MARKET RESEARCH:
{market_text}

Industry: {industry}

Provide comprehensive market analysis in JSON format."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error analyzing market landscape: {e}")
            return {"error": str(e)}
    
    async def generate_competitive_analysis(self,
                                          client_company: str,
                                          competitors: List[Dict[str, Any]],
                                          market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate competitive analysis and positioning"""
        try:
            # Prepare competitor data
            competitor_profiles = []
            for comp in competitors:
                profile = f"""
Company: {comp.get('name', 'Unknown')}
Description: {comp.get('description', 'No description')}
Strengths: {', '.join(comp.get('strengths', []))}
Weaknesses: {', '.join(comp.get('weaknesses', []))}
Market Position: {comp.get('market_position', 'Unknown')}
Key Products: {', '.join(comp.get('key_products', []))}
"""
                competitor_profiles.append(profile)
            
            competitors_text = "\n".join(competitor_profiles)
            
            system_prompt = """You are a strategic business consultant. Perform competitive analysis to help the client understand their position and opportunities.
            
            Return a JSON object with:
            {
                "competitive_positioning": {
                    "client_position": "description of client's current market position",
                    "differentiation_opportunities": ["opportunity1", "opportunity2"],
                    "competitive_gaps": ["gap1", "gap2"]
                },
                "threat_analysis": [
                    {
                        "competitor": "competitor name",
                        "threat_level": "high/medium/low",
                        "threat_type": "direct/indirect/potential",
                        "key_threats": ["threat1", "threat2"],
                        "mitigation_strategies": ["strategy1", "strategy2"]
                    }
                ],
                "opportunity_analysis": [
                    {
                        "opportunity": "opportunity description",
                        "potential_impact": "high/medium/low",
                        "feasibility": "high/medium/low",
                        "timeline": "short/medium/long term",
                        "requirements": ["requirement1", "requirement2"]
                    }
                ],
                "strategic_recommendations": [
                    {
                        "category": "category (e.g., product, marketing, operations)",
                        "recommendation": "specific recommendation",
                        "rationale": "why this recommendation",
                        "priority": "high/medium/low",
                        "estimated_impact": "description of expected impact"
                    }
                ]
            }"""
            
            user_prompt = f"""Perform competitive analysis for {client_company}.

CLIENT COMPANY: {client_company}

COMPETITORS:
{competitors_text}

MARKET ANALYSIS:
{json.dumps(market_analysis, indent=2)}

Provide strategic competitive analysis in JSON format."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating competitive analysis: {e}")
            return {"error": str(e)}
    
    async def generate_executive_summary(self,
                                       client_company: str,
                                       industry: str,
                                       competitors: List[Dict[str, Any]],
                                       market_analysis: Dict[str, Any],
                                       competitive_analysis: Dict[str, Any]) -> str:
        """Generate executive summary for the analysis"""
        try:
            system_prompt = """You are a senior business consultant writing an executive summary for a competitive analysis report.
            
            Write a comprehensive but concise executive summary that covers:
            1. Market overview and key findings
            2. Competitive landscape summary
            3. Key threats and opportunities
            4. Primary strategic recommendations
            
            The summary should be professional, actionable, and suitable for C-level executives.
            Aim for 300-500 words."""
            
            user_prompt = f"""Write an executive summary for the competitive analysis of {client_company} in the {industry} industry.
            
            Number of competitors analyzed: {len(competitors)}
            
            Market Analysis Summary:
            {json.dumps(market_analysis, indent=2)}
            
            Competitive Analysis Summary:
            {json.dumps(competitive_analysis, indent=2)}
            
            Focus on the most critical insights and actionable recommendations."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return f"Error generating executive summary: {str(e)}"