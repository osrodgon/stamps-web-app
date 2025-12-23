import os

# Environment variables. Use dotenv for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Application configuration
APP_NAME = "Stamps App"
LOG_LEVEL= os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE_NAME="frontend.log"
LOG_BASE_DIR="logs"

# Frontend
ASSETS_DIR="/assets"
ASSETS_FOLDER_NAME="assets"
BACKGROUND_IMG=f"{ASSETS_DIR}/background.webp"

# Backend
BACKEND_URL=f"http://{os.getenv("BACKEND_HOST", "localhost")}:8000/stamps_server/api/v1"
API_MASTER_KEY=os.getenv("API_MASTER_KEY")

