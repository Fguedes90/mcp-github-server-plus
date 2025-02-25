"""Main entry point for MPC GitHub Python."""

import os
import asyncio
from dotenv import load_dotenv
from .server import ServerConfig, run_server

def main() -> None:
    """Run the server."""
    # Load environment variables
    load_dotenv()
    
    # Create server config
    config = ServerConfig(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        github_token=os.getenv("GITHUB_TOKEN"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
    )
    
    # Run server
    asyncio.run(run_server(config))

if __name__ == "__main__":
    main() 