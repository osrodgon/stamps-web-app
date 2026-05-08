"""Application settings and configuration."""

import os
from pathlib import Path

# Environment variables. Use dotenv for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# User settings
STORAGE_PREFIX = "stamps_app."
USER_NAME = f"{STORAGE_PREFIX}username" 
USER_IS_ADMIN = f"{STORAGE_PREFIX}is_admin"
USER_FIRST_NAME = f"{STORAGE_PREFIX}first_name"
USER_LAST_NAME = f"{STORAGE_PREFIX}last_name"
USER_EMAIL = f"{STORAGE_PREFIX}email"
USER_JWT_TOKEN = f"{STORAGE_PREFIX}jwt_token"
USER_LANGUAGE = f"{STORAGE_PREFIX}language"
USER_ID = f"{STORAGE_PREFIX}id"

# Default language
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "es")  

# Application configuration
APP_NAME = "Stamps App"
LOG_LEVEL= os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE_NAME="frontend.log"
LOG_BASE_DIR="logs"

# Frontend
FRONTEND_PORT=8080
FRONTEND_DIR = Path(__file__).parent
ASSETS_DIR = f"{FRONTEND_DIR}/assets"
BACKGROUND_IMG="background.webp"
FAV_ICON="fav_icon.webp"
ORG_LOGO="org.webp"
NO_STAMP = "no_stamp.webp"
FAV_ICON="fav_icon.webp"
MOCK_LOGIN = str(os.getenv("MOCK_LOGIN_ENABLED", "False")).lower() == 'true'
MOCK_USER = os.getenv("MOCK_LOGIN_USER", "none")
MOCK_PASSWORD = os.getenv("MOCK_LOGIN_PASSWORD", "none")


# Backend
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
BACKEND_SERVER_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
BACKEND_URL=f"{BACKEND_SERVER_URL}/stamps-backend/api/v1"
API_MASTER_KEY=os.getenv("API_MASTER_KEY")

# Images
IMAGE_DIR = f"{ASSETS_DIR}/stamps-data/images"

# Fonts
FONT_REGULAR = "fonts/Roboto-Regular.ttf"
FONT_BOLD = "fonts/Roboto-Bold.ttf"
FONT_BLACK = "fonts/Roboto-Black.ttf"

