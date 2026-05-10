"""
URL definitions for backend API and frontend routes.

This module provides centralized URL constants for both the backend
API endpoints and frontend navigation routes. The URLs are constructed
from the BACKEND_URL setting.

Example:
    from core.urls import URLs
    # Backend API
    login_url = URLs.Backend.login
    # Frontend route
    login_route = URLs.Frontend.login
"""

from settings import BACKEND_URL


class URLs:
    """Container for backend and frontend URL constants.

    This class is organized into two inner classes:
    - Backend: API endpoint URLs for the Django REST API
    - Frontend: Route paths for client-side navigation
    """

    class Backend:
        """Backend API endpoint URLs.

        Contains all API endpoints for the stamps backend.
        These are prefixed with BACKEND_URL from settings.
        """
        login =                 f"{BACKEND_URL}/login/"
        logout =                f"{BACKEND_URL}/logoff/"
        issues =                f"{BACKEND_URL}/issues/"
        print_types =           f"{BACKEND_URL}/print_types/"
        signup =                f"{BACKEND_URL}/users/"
        stamps =                f"{BACKEND_URL}/stamps/"
        stamp_types =           f"{BACKEND_URL}/stamps_type/"
        years =                 f"{BACKEND_URL}/years/"
        config =                f"{BACKEND_URL}/config/"
        issues_extraction =     f"{BACKEND_URL}/issues/extraction/"
        issues_collections =    f"{BACKEND_URL}/issues/collections/"
        
    class Frontend:
        """Frontend route paths.

        Contains all client-side navigation routes.
        These paths are used with page.push_route() for navigation.
        """

        collections =           "/collections"
        login =                 "/login"
        logout =                "/logout"
        root =                  "/"
        signup =                "/signup"
        stamps_manager =        "/admin/stamps/manager"
        not_found =             "/404"