import os

# Application configuration
LOG_LEVEL="DEBUG"
LOG_FILE_NAME="frontend.log"
LOG_BASE_DIR="logs"

# Frontend
ASSETS_DIR="/assets"
BACKGROUND_IMG=f"{ASSETS_DIR}/background.png"

# Backend
BACKEND_URL=os.getenv("BACKEND_URL", "http://localhost:8000/stamps_server/api/v1")