"""
Application settings and configuration.

This module centralizes all configuration settings for the Stamps web
application frontend. It includes:

- User preference keys for SharedPreferences storage
- Application metadata (name, ports, directories)
- Backend API configuration
- Asset paths (fonts, images)
- Environment variable loading with dotenv support

All settings are loaded from environment variables with sensible defaults
for local development.

Example:
    >>> from settings import APP_NAME, BACKEND_URL
    >>> print(APP_NAME)
    'Stamps App'
"""

import os
from pathlib import Path

# --- Environment Setup ---
# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# --- User Preference Keys ---
# Keys used for storing user data in SharedPreferences.
# All keys are prefixed with STORAGE_PREFIX to avoid conflicts.
STORAGE_PREFIX = "stamps_app."
USER_NAME = f"{STORAGE_PREFIX}username"
USER_IS_ADMIN = f"{STORAGE_PREFIX}is_admin"
USER_FIRST_NAME = f"{STORAGE_PREFIX}first_name"
USER_LAST_NAME = f"{STORAGE_PREFIX}last_name"
USER_EMAIL = f"{STORAGE_PREFIX}email"
USER_JWT_TOKEN = f"{STORAGE_PREFIX}jwt_token"
USER_LANGUAGE = f"{STORAGE_PREFIX}language"
USER_ID = f"{STORAGE_PREFIX}id"
TIMEZONE = f"{STORAGE_PREFIX}_timezone"


# --- Application Defaults ---
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "es")  # Default: Spanish
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")


# --- Application Metadata ---
APP_NAME = "Stamps App"
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE_NAME = "frontend.log"
LOG_BASE_DIR = "logs"


# --- Frontend Configuration ---
FRONTEND_PORT = 8080
FRONTEND_DIR = Path(__file__).parent
ASSETS_DIR = f"{FRONTEND_DIR}/assets"
BACKGROUND_IMG = "background.webp"
FAV_ICON = "fav_icon.webp"
ORG_LOGO = "org.png"
NO_STAMP = "no_stamp_new.webp"

# Mock login for development/testing
MOCK_LOGIN = str(os.getenv("MOCK_LOGIN_ENABLED", "False")).lower() == 'true'
MOCK_USER = os.getenv("MOCK_LOGIN_USER", "none")
MOCK_PASSWORD = os.getenv("MOCK_LOGIN_PASSWORD", "none")


# --- Backend API Configuration ---
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
BACKEND_SERVER_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
BACKEND_URL = f"{BACKEND_SERVER_URL}/stamps-backend/api/v1"
API_MASTER_KEY = os.getenv("API_MASTER_KEY")


# --- Asset Paths ---
IMAGE_DIR = f"{ASSETS_DIR}/stamps"

# Font files (relative to ASSETS_DIR)
FONT_REGULAR = "fonts/Roboto-Regular.ttf"
FONT_BOLD = "fonts/Roboto-Bold.ttf"
FONT_BLACK = "fonts/Roboto-Black.ttf"

