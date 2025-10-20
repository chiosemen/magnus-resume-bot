"""
Entry point script for running the Streamlit dashboard locally.

This script starts the Streamlit application.
"""

import sys
import subprocess
from pathlib import Path

if __name__ == "__main__":
    print("Starting Magnus Resume Bot Dashboard...")
    print("Dashboard will be available at: http://localhost:8501")
    print("Press CTRL+C to stop the server\n")

    # Run streamlit
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app.py",
        "--server.port=8501",
        "--server.headless=true"
    ])
