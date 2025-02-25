"""FastAPI application for MPC GitHub Python."""

import os
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from mcp.fastmcp import FastMCP
from .handlers import GitHubHandler

class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    github_token: Optional[str] = None
    debug: bool = False

def create_app(config: Optional[ServerConfig] = None) -> FastAPI:
    """Create FastAPI application.
    
    Args:
        config: Server configuration
        
    Returns:
        FastAPI application
    """
    if config is None:
        config = ServerConfig(
            github_token=os.getenv("GITHUB_TOKEN"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )
    
    # Create FastMCP app
    app = FastMCP(
        title="MPC GitHub Python",
        description="A Python implementation of GitHub operations using MPC",
        version="0.1.0",
        debug=config.debug,
    )
    
    # Register GitHub handler
    handler = GitHubHandler(token=config.github_token)
    app.register_handler("github", handler)
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok"}
    
    return app

async def run_server(config: Optional[ServerConfig] = None) -> None:
    """Run the server.
    
    Args:
        config: Server configuration
    """
    import uvicorn
    
    if config is None:
        config = ServerConfig(
            github_token=os.getenv("GITHUB_TOKEN"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )
    
    app = create_app(config)
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="debug" if config.debug else "info",
    ) 