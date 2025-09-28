import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='.env')

from database.connection import startup_event, shutdown_event
from database.repositories import AnalysisRepository, ReportRepository
from services.tavily_service import TavilyService
from services.redis_service import RedisService
from services.llm_service import LLMService
from agents.coordinator import CompetitorAnalysisCoordinator

from api.routes.analysis import router as analysis_router
from api.routes.reports import router as reports_router
from api.routes.websocket import router as websocket_router
from api.routes.products import router as products_router


# Global services
analysis_repository = AnalysisRepository()
report_repository = ReportRepository()
tavily_service = None
redis_service = None
llm_service = None
coordinator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global tavily_service, redis_service, llm_service, coordinator

    # Startup
    logger.info("Starting Competitor Analysis System...")

    try:
        # Initialize database
        await startup_event()

        # Initialize services
        tavily_service = TavilyService()
        redis_service = RedisService()
        await redis_service.connect()
        llm_service = LLMService()

        # Initialize coordinator
        coordinator = CompetitorAnalysisCoordinator(
            tavily_service=tavily_service,
            redis_service=redis_service,
            llm_service=llm_service,
            analysis_repository=analysis_repository,
            report_repository=report_repository
        )

        # Make services available to routes
        app.state.coordinator = coordinator
        app.state.analysis_repository = analysis_repository
        app.state.report_repository = report_repository
        app.state.redis_service = redis_service

        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")

    try:
        if redis_service:
            await redis_service.disconnect()
        await shutdown_event()
        logger.info("Shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="Competitor Analysis System",
    description="AI-powered competitive analysis platform using multi-agent workflows",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Competitor Analysis System is running",
        "version": "1.0.0"
    }


# Include routers
app.include_router(analysis_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(reports_router, prefix="/api/v1", tags=["Reports"])
app.include_router(products_router, prefix="/api/v1", tags=["Products"])
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])

# Serve static files if enabled
if os.getenv("SERVE_STATIC_FILES", "false").lower() == "true":
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        # Serve React app at root
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Competitor Analysis System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    # Configure logging
    logger.add(
        "logs/api.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )

    # Run the application
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG_MODE", "False").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
