#!/usr/bin/env python3
"""
Uvicorn server startup script for the Competitor Analysis System
"""
import uvicorn
import os
from pathlib import Path

def main():
    """Main entry point for the uvicorn server"""
    # Set the backend directory as the working directory
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Run uvicorn with the FastAPI app
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend"],
        log_level="info"
    )

if __name__ == "__main__":
    main()