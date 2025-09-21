import os
from typing import List, Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Competitor Analysis System"
    app_version: str = "1.0.0"
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Database
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "competitor_analysis"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # External APIs
    openai_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    
    # LLM Settings
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4000
    
    # Analysis Settings
    max_competitors_per_analysis: int = 20
    max_parallel_agents: int = 5
    analysis_timeout_seconds: int = 14400  # 4 hours
    data_cache_ttl_seconds: int = 3600  # 1 hour
    
    # Tavily Settings
    tavily_max_results: int = 10
    tavily_search_depth: str = "advanced"
    tavily_include_domains: List[str] = []
    tavily_exclude_domains: List[str] = []
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 100
    
    # Security
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()