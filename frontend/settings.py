import os

# Application configuration
APP_NAME = "Stamps App"
LOG_LEVEL="DEBUG"
LOG_FILE_NAME="frontend.log"
LOG_BASE_DIR="logs"

# Frontend
ASSETS_DIR="/assets"
ASSETS_FOLDER_NAME="assets"
BACKGROUND_IMG=f"{ASSETS_DIR}/background.png"

# Backend
BACKEND_URL=f"http://{os.getenv("BACKEND_HOST", "localhost")}:8000/stamps_server/api/v1"

