"""
Entry point script for running the FastAPI application locally.

This script starts the FastAPI server using uvicorn.
"""

import uvicorn
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("Starting Magnus Resume Bot API...")
    print("API will be available at: http://localhost:8000")
    print("Interactive docs at: http://localhost:8000/docs")
    print("Press CTRL+C to stop the server\n")

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
