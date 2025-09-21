import json
import asyncio
from typing import Any, Optional, List, Dict
import redis.asyncio as redis
from loguru import logger
import os


class RedisService:
    """Service for Redis caching and session management"""
    
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.default_ttl = int(os.getenv("DATA_CACHE_TTL_SECONDS", "3600"))
        
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True
            )
            
            # Test connection
            await self.client.ping()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")
    
    async def _ensure_connected(self):
        """Ensure Redis connection is active"""
        if self.client is None:
            await self.connect()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in Redis with optional TTL"""
        try:
            await self._ensure_connected()
            
            # Serialize value to JSON
            serialized_value = json.dumps(value, default=str)
            
            ttl = ttl or self.default_ttl
            result = await self.client.setex(key, ttl, serialized_value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error setting Redis key '{key}': {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis"""
        try:
            await self._ensure_connected()
            
            value = await self.client.get(key)
            
            if value is None:
                return None
            
            # Deserialize JSON value
            return json.loads(value)
            
        except Exception as e:
            logger.error(f"Error getting Redis key '{key}': {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        try:
            await self._ensure_connected()
            
            result = await self.client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting Redis key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            await self._ensure_connected()
            
            result = await self.client.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Error checking Redis key '{key}': {e}")
            return False
    
    async def get_keys_pattern(self, pattern: str) -> List[str]:
        """Get all keys matching a pattern"""
        try:
            await self._ensure_connected()
            
            keys = await self.client.keys(pattern)
            return keys
            
        except Exception as e:
            logger.error(f"Error getting keys with pattern '{pattern}': {e}")
            return []
    
    # Caching methods for specific data types
    
    async def cache_search_results(self, 
                                 query_hash: str, 
                                 results: List[Dict[str, Any]], 
                                 ttl: Optional[int] = None) -> bool:
        """Cache search results"""
        key = f"search:{query_hash}"
        return await self.set(key, results, ttl)
    
    async def get_cached_search_results(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results"""
        key = f"search:{query_hash}"
        return await self.get(key)
    
    async def cache_competitor_data(self, 
                                  company_name: str, 
                                  data: Dict[str, Any], 
                                  ttl: Optional[int] = None) -> bool:
        """Cache competitor data"""
        key = f"competitor:{company_name.lower().replace(' ', '_')}"
        return await self.set(key, data, ttl)
    
    async def get_cached_competitor_data(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Get cached competitor data"""
        key = f"competitor:{company_name.lower().replace(' ', '_')}"
        return await self.get(key)
    
    async def cache_market_analysis(self, 
                                  industry: str, 
                                  target_market: str, 
                                  data: Dict[str, Any], 
                                  ttl: Optional[int] = None) -> bool:
        """Cache market analysis data"""
        key = f"market:{industry.lower().replace(' ', '_')}:{target_market.lower().replace(' ', '_')}"
        return await self.set(key, data, ttl)
    
    async def get_cached_market_analysis(self, 
                                       industry: str, 
                                       target_market: str) -> Optional[Dict[str, Any]]:
        """Get cached market analysis data"""
        key = f"market:{industry.lower().replace(' ', '_')}:{target_market.lower().replace(' ', '_')}"
        return await self.get(key)
    
    async def cache_agent_state(self, 
                              request_id: str, 
                              state: Dict[str, Any], 
                              ttl: Optional[int] = None) -> bool:
        """Cache agent state"""
        key = f"agent_state:{request_id}"
        # Use longer TTL for agent states (24 hours by default)
        ttl = ttl or 86400
        return await self.set(key, state, ttl)
    
    async def get_cached_agent_state(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get cached agent state"""
        key = f"agent_state:{request_id}"
        return await self.get(key)
    
    async def delete_agent_state(self, request_id: str) -> bool:
        """Delete cached agent state"""
        key = f"agent_state:{request_id}"
        return await self.delete(key)
    
    # Session and progress tracking
    
    async def set_analysis_progress(self, 
                                  request_id: str, 
                                  progress: int, 
                                  status: str, 
                                  current_stage: str) -> bool:
        """Set analysis progress for real-time updates"""
        key = f"progress:{request_id}"
        data = {
            "progress": progress,
            "status": status,
            "current_stage": current_stage,
            "updated_at": str(asyncio.get_event_loop().time())
        }
        # Short TTL for progress updates
        return await self.set(key, data, 300)  # 5 minutes
    
    async def get_analysis_progress(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis progress"""
        key = f"progress:{request_id}"
        return await self.get(key)
    
    async def store_progress_update(self, request_id: str, progress_update: Dict[str, Any]) -> bool:
        """Store progress update for real-time display"""
        key = f"progress_update:{request_id}"
        # Store with 1 hour TTL to prevent accumulation
        return await self.set(key, progress_update, ttl=3600)
    
    async def store_analysis_result(self, request_id: str, result: Dict[str, Any]) -> bool:
        """Store final analysis result"""
        key = f"analysis_result:{request_id}"
        # Store with 24 hour TTL
        return await self.set(key, result, ttl=86400)
    
    async def get_cached_analysis_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result"""
        key = f"analysis_result:{request_id}"
        return await self.get(key)
    
    async def store_human_review_data(self, request_id: str, review_data: Dict[str, Any]) -> bool:
        """Store human review data for frontend interface"""
        key = f"human_review:{request_id}"
        # Store with 2 hour TTL - enough time for human review
        return await self.set(key, review_data, ttl=7200)
    
    async def get_human_review_data(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get human review data for frontend"""
        key = f"human_review:{request_id}"
        return await self.get(key)
    
    async def clear_human_review_data(self, request_id: str) -> bool:
        """Clear human review data after decision is made"""
        key = f"human_review:{request_id}"
        return await self.delete(key)
    
    async def set_progress_message(self, request_id: str, message: str) -> bool:
        """Set current progress message for workflow visualization"""
        key = f"progress_message:{request_id}"
        data = {
            "message": message,
            "timestamp": str(asyncio.get_event_loop().time())
        }
        # Short TTL for progress messages
        return await self.set(key, data, 300)  # 5 minutes
    
    async def get_progress_message(self, request_id: str) -> Optional[str]:
        """Get current progress message"""
        key = f"progress_message:{request_id}"
        data = await self.get(key)
        return data.get("message") if data else None
    
    # Rate limiting support
    
    async def increment_rate_limit(self, identifier: str, window_seconds: int = 60) -> int:
        """Increment rate limit counter"""
        try:
            await self._ensure_connected()
            
            key = f"rate_limit:{identifier}"
            
            # Use pipeline for atomic operations
            async with self.client.pipeline(transaction=True) as pipe:
                await pipe.incr(key)
                await pipe.expire(key, window_seconds)
                results = await pipe.execute()
                
                return results[0]  # Return the incremented value
                
        except Exception as e:
            logger.error(f"Error incrementing rate limit for '{identifier}': {e}")
            return 0
    
    async def get_rate_limit_count(self, identifier: str) -> int:
        """Get current rate limit count"""
        try:
            await self._ensure_connected()
            
            key = f"rate_limit:{identifier}"
            count = await self.client.get(key)
            
            return int(count) if count else 0
            
        except Exception as e:
            logger.error(f"Error getting rate limit count for '{identifier}': {e}")
            return 0