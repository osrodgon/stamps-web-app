import os

# Environment variables. Use dotenv for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# User settings
USER_NAME = 'username'
USER_IS_ADMIN = 'is_admin'
USER_FIRST_NAME = 'first_name'
USER_LAST_NAME = 'last_name'
USER_EMAIL = 'email'
USER_JWT_TOKEN = 'jwt_token'
USER_LANGUAGE = 'language'
USER_ID = 'id'

# Default language
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "es")  

# Application configuration
APP_NAME = "Stamps App"
LOG_LEVEL= os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE_NAME="frontend.log"
LOG_BASE_DIR="logs"

# Frontend
ASSETS_DIR="/assets"
ASSETS_FOLDER_NAME="assets"
BACKGROUND_IMG=f"{ASSETS_DIR}/background.webp"
ORG_LOGO=f"{ASSETS_DIR}/org.webp"
NO_STAMP = f"{ASSETS_DIR}/no_stamp.webp"
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

