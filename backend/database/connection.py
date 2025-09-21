import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from loguru import logger


class DatabaseConnection:
    client: Optional[AsyncIOMotorClient] = None
    database = None


db_connection = DatabaseConnection()


async def get_database():
    """Get the database instance"""
    if db_connection.database is None:
        await init_database()
    return db_connection.database


async def init_database():
    """Initialize database connection"""
    try:
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        database_name = os.getenv("MONGODB_DATABASE", "competitor_analysis")
        
        logger.info(f"Connecting to MongoDB at {mongodb_uri}")
        
        # Create client
        db_connection.client = AsyncIOMotorClient(mongodb_uri)
        
        # Test connection
        await db_connection.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Get database
        db_connection.database = db_connection.client[database_name]
        
        # Create indexes
        await create_indexes()
        
        logger.info(f"Database '{database_name}' initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_database():
    """Close database connection"""
    if db_connection.client:
        db_connection.client.close()
        logger.info("Database connection closed")


async def create_indexes():
    """Create database indexes for better performance"""
    try:
        db = db_connection.database
        
        # Analysis collection indexes
        await db.analyses.create_index("request_id", unique=True)
        await db.analyses.create_index("client_company")
        await db.analyses.create_index("industry")
        await db.analyses.create_index("status")
        await db.analyses.create_index("created_at")
        
        # Reports collection indexes
        await db.reports.create_index("analysis_id")
        await db.reports.create_index("client_company")
        await db.reports.create_index("created_at")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"Error creating indexes: {e}")


# Event handlers for FastAPI
async def startup_event():
    """Database startup event handler"""
    await init_database()


async def shutdown_event():
    """Database shutdown event handler"""
    await close_database()