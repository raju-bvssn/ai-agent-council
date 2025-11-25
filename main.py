"""
Main entry point for Agent Council API server.

Run with: uvicorn main:app --reload
"""

import uvicorn

from app.app import app
from app.utils.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "app.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )

