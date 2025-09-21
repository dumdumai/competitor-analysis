import asyncio
from typing import Dict, Any, List
from loguru import logger
from models.agent_state import AgentState
from models.analysis import CompetitorData
from services.llm_service import LLMService


class DataProcessingAgent:
    """Agent responsible for processing and structuring collected competitor data"""
    
    def __init__(self, llm_service: LLMService):
        self.name = "data_processing"
        self.llm_service = llm_service
        self.max_concurrent_processing = 2
    
    async def process(self, state: AgentState) -> AgentState:
        """Process and structure collected competitor data"""
        try:
            logger.info(f"Starting data processing for {len(state.discovered_competitors)} competitors")
            
            # Update progress
            state.update_progress("data_processing", 20)
            
            # Get collected data
            collected_data = state.search_results.get("data_collection", {})
            
            if not collected_data:
                state.add_warning("No collected data found to process")
                state.complete_stage("data_processing")
                return state
            
            # Process competitor data using LLM
            processed_competitors = await self._process_competitors_batch(
                collected_data, state
            )
            
            # Add processed data to state
            for competitor_data in processed_competitors:
                if competitor_data:
                    state.add_competitor_data(competitor_data)
            
            # Store processed data for reference
            state.processed_data["competitors"] = [
                comp.dict() for comp in state.competitor_data
            ]
            
            # Update metadata
            state.metadata.update({
                "processed_competitors": len(state.competitor_data),
                "successful_processing": len([c for c in processed_competitors if c]),
                "processing_completed": True
            })
            
            # Complete the stage
            state.complete_stage("data_processing")
            state.update_progress("data_processing", 100)
            
            logger.info(f"Data processing completed for {len(state.competitor_data)} competitors")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in data processing: {e}")
            state.add_error(f"Data processing failed: {str(e)}")
            return state
    
    async def _process_competitors_batch(self, 
                                       collected_data: Dict[str, List[Dict[str, Any]]], 
                                       state: AgentState) -> List[CompetitorData]:
        """Process competitors in batches to manage resource usage"""
        processed_competitors = []
        competitor_names = list(collected_data.keys())
        total_competitors = len(competitor_names)
        
        # Process in smaller batches
        for i in range(0, total_competitors, self.max_concurrent_processing):
            batch = competitor_names[i:i + self.max_concurrent_processing]
            
            # Update progress
            progress = 20 + int((i / total_competitors) * 75)
            state.update_progress("data_processing", progress)
            
            # Process batch concurrently
            batch_tasks = [
                self._process_single_competitor(
                    competitor_name, 
                    collected_data[competitor_name], 
                    state
                )
                for competitor_name in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle results
            for j, result in enumerate(batch_results):
                competitor_name = batch[j]
                
                if isinstance(result, Exception):
                    logger.error(f"Error processing {competitor_name}: {result}")
                    state.add_warning(f"Failed to process {competitor_name}: {str(result)}")
                    processed_competitors.append(None)
                else:
                    processed_competitors.append(result)
            
            # Small delay between batches
            if i + self.max_concurrent_processing < total_competitors:
                await asyncio.sleep(1)
        
        return processed_competitors
    
    async def _process_single_competitor(self, 
                                       competitor_name: str, 
                                       search_results: List[Dict[str, Any]], 
                                       state: AgentState) -> CompetitorData:
        """Process data for a single competitor using LLM extraction"""
        try:
            logger.info(f"Processing data for {competitor_name}")
            
            if not search_results:
                logger.warning(f"No search results for {competitor_name}")
                return self._create_minimal_competitor_data(competitor_name)
            
            # Use LLM to extract structured information
            extracted_info = await self.llm_service.extract_competitor_info(
                competitor_name, search_results
            )
            
            # Convert to CompetitorData model
            competitor_data = self._convert_to_competitor_data(
                extracted_info, competitor_name, state
            )
            
            logger.info(f"Successfully processed {competitor_name}")
            return competitor_data
            
        except Exception as e:
            logger.error(f"Error processing {competitor_name}: {e}")
            # Return minimal data instead of failing completely
            return self._create_minimal_competitor_data(competitor_name, error=str(e))
    
    def _convert_to_competitor_data(self, 
                                  extracted_info: Dict[str, Any], 
                                  competitor_name: str, 
                                  state: AgentState) -> CompetitorData:
        """Convert extracted information to CompetitorData model"""
        try:
            # Handle potential LLM extraction errors
            if "error" in extracted_info:
                logger.warning(f"LLM extraction error for {competitor_name}: {extracted_info['error']}")
                return self._create_minimal_competitor_data(competitor_name, extracted_info.get("error"))
            
            # Build CompetitorData with safe field extraction
            competitor_data = CompetitorData(
                name=extracted_info.get("name", competitor_name),
                website=extracted_info.get("website"),
                description=extracted_info.get("description", "No description available"),
                business_model=extracted_info.get("business_model", "Unknown"),
                target_market=extracted_info.get("target_market", state.analysis_context.target_market),
                founding_year=self._safe_int_convert(extracted_info.get("founding_year")),
                headquarters=extracted_info.get("headquarters"),
                employee_count=extracted_info.get("employee_count"),
                funding_info=extracted_info.get("funding_info"),
                key_products=extracted_info.get("key_products", []),
                pricing_strategy=extracted_info.get("pricing_strategy"),
                market_position=extracted_info.get("market_position"),
                strengths=extracted_info.get("strengths", []),
                weaknesses=extracted_info.get("weaknesses", []),
                recent_news=extracted_info.get("recent_news", []),
                social_media_presence=extracted_info.get("social_media_presence", {}),
                financial_data=extracted_info.get("financial_data"),
                technology_stack=extracted_info.get("technology_stack", []),
                partnerships=extracted_info.get("partnerships", []),
                competitive_advantages=extracted_info.get("competitive_advantages", []),
                market_share=self._safe_float_convert(extracted_info.get("market_share")),
                growth_trajectory=extracted_info.get("growth_trajectory")
            )
            
            return competitor_data
            
        except Exception as e:
            logger.error(f"Error converting data for {competitor_name}: {e}")
            return self._create_minimal_competitor_data(competitor_name, str(e))
    
    def _create_minimal_competitor_data(self, 
                                      competitor_name: str, 
                                      error: str = None) -> CompetitorData:
        """Create minimal competitor data when processing fails"""
        return CompetitorData(
            name=competitor_name,
            description=f"Data processing failed{': ' + error if error else ''}",
            business_model="Unknown",
            target_market="Unknown",
            strengths=[],
            weaknesses=["Insufficient data available"],
            key_products=[],
            competitive_advantages=[],
            technology_stack=[],
            partnerships=[],
            recent_news=[]
        )
    
    def _safe_int_convert(self, value) -> int:
        """Safely convert value to integer"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Extract numeric part if it's a string like "2020" or "Founded in 2020"
                import re
                numbers = re.findall(r'\d{4}', value)
                if numbers:
                    return int(numbers[0])
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_float_convert(self, value) -> float:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Remove percentage signs and other characters
                import re
                numbers = re.findall(r'\d+\.?\d*', value.replace('%', ''))
                if numbers:
                    return float(numbers[0])
            return float(value)
        except (ValueError, TypeError):
            return None
    
    async def process_market_data(self, 
                                market_search_results: List[Dict[str, Any]], 
                                state: AgentState) -> Dict[str, Any]:
        """Process market analysis data"""
        try:
            logger.info("Processing market analysis data")
            
            if not market_search_results:
                return {"error": "No market data to process"}
            
            # Use LLM to analyze market landscape
            market_analysis = await self.llm_service.analyze_market_landscape(
                industry=state.analysis_context.industry,
                competitors=[comp.dict() for comp in state.competitor_data],
                search_results=market_search_results
            )
            
            # Store in processed data
            state.processed_data["market_analysis"] = market_analysis
            
            logger.info("Market data processing completed")
            return market_analysis
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
            return {"error": str(e)}