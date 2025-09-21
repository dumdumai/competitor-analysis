import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request, Query
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

from models.product import (
    ProductComparisonRequest, 
    ProductData, 
    ProductComparison,
    ProductComparisonResult
)
from models.analysis import AnalysisRequest
from agents.coordinator import CompetitorAnalysisCoordinator
from database.repositories import AnalysisRepository


router = APIRouter()


class ProductUpdateRequest(BaseModel):
    """Request model for updating product details"""
    product_id: str
    updates: Dict[str, Any]


def get_coordinator(request: Request) -> CompetitorAnalysisCoordinator:
    """Dependency to get coordinator from app state"""
    return request.app.state.coordinator


def get_analysis_repository(request: Request) -> AnalysisRepository:
    """Dependency to get analysis repository from app state"""
    return request.app.state.analysis_repository


@router.post("/product-comparison", response_model=dict)
async def start_product_comparison(
    comparison_request: ProductComparisonRequest,
    background_tasks: BackgroundTasks,
    coordinator: CompetitorAnalysisCoordinator = Depends(get_coordinator)
):
    """
    Start a new product comparison analysis
    
    This endpoint initiates a product-specific comparison workflow that includes:
    - Product discovery and identification
    - Feature comparison
    - Pricing analysis
    - Performance benchmarking
    - User review aggregation
    - Competitive positioning
    - Recommendation generation
    """
    try:
        logger.info(f"Starting product comparison for {comparison_request.client_product}")
        
        # Validate request
        if not comparison_request.client_product.strip():
            raise HTTPException(status_code=400, detail="Client product name is required")
        
        if not comparison_request.product_category.strip():
            raise HTTPException(status_code=400, detail="Product category is required")
        
        # Convert to AnalysisRequest for compatibility with existing workflow
        analysis_request = AnalysisRequest(
            client_company=comparison_request.client_company,
            industry=comparison_request.product_category,  # Use category as industry
            target_market=comparison_request.target_market,
            business_model="Product-based",  # Default for product comparisons
            specific_requirements=comparison_request.specific_requirements,
            max_competitors=comparison_request.max_products,
            comparison_type="product",
            client_product=comparison_request.client_product,
            product_category=comparison_request.product_category,
            comparison_criteria=comparison_request.comparison_criteria
        )
        
        # Create the analysis record
        request_id = await coordinator.analysis_repository.create_analysis(analysis_request)
        
        # Start analysis workflow in background
        background_tasks.add_task(run_product_comparison_workflow, coordinator, analysis_request, request_id)
        
        return {
            "message": "Product comparison started successfully",
            "request_id": request_id,
            "status": "initiated",
            "client_product": comparison_request.client_product,
            "product_category": comparison_request.product_category,
            "comparison_type": "product",
            "estimated_duration": "10-20 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting product comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products", response_model=List[ProductData])
async def get_products(
    category: Optional[str] = Query(None, description="Filter by product category"),
    company: Optional[str] = Query(None, description="Filter by company"),
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    repository: AnalysisRepository = Depends(get_analysis_repository)
):
    """
    Get list of products from the database
    
    Optionally filter by category or company
    """
    try:
        # This would need to be implemented in the repository
        # For now, return empty list as placeholder
        logger.info(f"Fetching products - category: {category}, company: {company}, limit: {limit}")
        
        # TODO: Implement product retrieval from database
        products = []
        
        return products
        
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}", response_model=ProductData)
async def get_product(
    product_id: str,
    repository: AnalysisRepository = Depends(get_analysis_repository)
):
    """
    Get detailed information about a specific product
    """
    try:
        logger.info(f"Fetching product details for ID: {product_id}")
        
        # TODO: Implement product retrieval from database
        # For now, raise not found
        raise HTTPException(status_code=404, detail="Product not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/products/{product_id}", response_model=dict)
async def update_product(
    product_id: str,
    update_request: ProductUpdateRequest,
    repository: AnalysisRepository = Depends(get_analysis_repository)
):
    """
    Update product details
    
    Allows updating specific fields of a product without replacing the entire document
    """
    try:
        logger.info(f"Updating product {product_id} with: {update_request.updates}")
        
        # Validate that product_id in request matches path parameter
        if update_request.product_id != product_id:
            raise HTTPException(
                status_code=400, 
                detail="Product ID in request body does not match URL parameter"
            )
        
        # TODO: Implement product update in database
        # For now, return success message
        return {
            "message": "Product updated successfully",
            "product_id": product_id,
            "updated_fields": list(update_request.updates.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/{product_id}/compare/{competitor_product_id}", response_model=ProductComparison)
async def compare_products(
    product_id: str,
    competitor_product_id: str,
    criteria: Optional[List[str]] = Query(None, description="Specific comparison criteria"),
    repository: AnalysisRepository = Depends(get_analysis_repository)
):
    """
    Perform a direct comparison between two products
    
    This provides a quick comparison without running the full analysis workflow
    """
    try:
        logger.info(f"Comparing products: {product_id} vs {competitor_product_id}")
        
        # TODO: Implement direct product comparison
        # This would fetch both products and generate a comparison
        
        raise HTTPException(status_code=501, detail="Direct product comparison not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product-comparisons/{request_id}", response_model=ProductComparisonResult)
async def get_product_comparison_results(
    request_id: str,
    repository: AnalysisRepository = Depends(get_analysis_repository)
):
    """
    Get results of a product comparison analysis
    """
    try:
        logger.info(f"Fetching product comparison results for request: {request_id}")
        
        # Fetch the analysis result
        result = await repository.get_analysis_result(request_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Product comparison not found")
        
        # Check if it's a product comparison
        if result.get("comparison_type") != "product":
            raise HTTPException(
                status_code=400, 
                detail="This request ID is not for a product comparison"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product comparison results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_product_comparison_workflow(
    coordinator: CompetitorAnalysisCoordinator,
    analysis_request: AnalysisRequest,
    request_id: str
):
    """
    Run the product comparison workflow asynchronously
    """
    try:
        logger.info(f"Starting product comparison workflow for request {request_id}")
        
        # Run the analysis workflow with product-specific context
        result = await coordinator.analyze_competitors_with_id(analysis_request, request_id)
        
        logger.info(f"Product comparison workflow completed for request {request_id}")
        
    except Exception as e:
        logger.error(f"Product comparison workflow failed: {e}")
        # Update the analysis status to failed
        await coordinator.analysis_repository.update_analysis(
            request_id, 
            {
                "status": "failed", 
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }
        )