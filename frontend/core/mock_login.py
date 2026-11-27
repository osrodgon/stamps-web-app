"""Automatic login for development, driven by `MOCK_LOGIN_*` (2026-11-26).

The Flet migration dropped the old `mock_login()` from the login page and left the
three settings orphaned: `MOCK_LOGIN_ENABLED=true` did nothing. This class restores
the behaviour in Flet: at startup, when the flag is on, it logs in with the
credentials from the environment, stores the token and returns the route the app
should open.

It is **development only**. The flag defaults to false, `.env.example` documents it
with a false value, and `run()` refuses to do anything unless it is on.
"""

from __future__ import annotations

from typing import Optional

import requests

from core.base_ui import BaseUI
from core.urls import URLs
from services.auth_service import AuthService
from settings import MOCK_LOGIN, MOCK_PASSWORD, MOCK_USER


class MockLogin(BaseUI):
    """Log in with the environment's credentials, once, for development.

    Usage (in `main`, only when the flag is on):
        route = await MockLogin().run()
    """

    def __init__(self, service: Optional[AuthService] = None) -> None:
        """Take the auth service, or build the default one."""
        super().__init__()
        self._service: AuthService = service or AuthService()

    async def run(self) -> Optional[str]:
        """Log in and store the session.

        Returns:
            The route the app should open, or None when the mock login is off,
            misconfigured or refused by the backend.
        """
        if not MOCK_LOGIN or not MOCK_USER or not MOCK_PASSWORD:
            self.log.debug("Mock login is off or not configured.")
            return None

        self.log.debug(f"Mock login as {MOCK_USER}.")
        response = await self._service.login(
            {"username": MOCK_USER, "password": MOCK_PASSWORD}
        )

        if response is None or response.status_code != requests.codes.ok:
            self.log.error("Mock login failed: no valid answer from the backend.")
            return None

        data = response.json().get("data") or {}
        token = data.get("token")
        user_data = data.get("payload")
        if not token or not user_data:
            self.log.error("Mock login failed: the answer carries no session.")
            return None

        await self._save_user(token, user_data)

        return (
            URLs.Frontend.stamps_manager
            if user_data.get("is_admin")
            else URLs.Frontend.collections
        )
