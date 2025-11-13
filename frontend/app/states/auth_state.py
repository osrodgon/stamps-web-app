import reflex as rx
from typing import TypedDict, Optional
import hashlib
import json
import re


class User(TypedDict):
    email: str
    password_hash: str


class Session(TypedDict):
    email: str


class AuthState(rx.State):
    """Manages user authentication, registration, and session state."""

    users_json: str = rx.LocalStorage("[]", name="auth_users")
    session_json: str = rx.LocalStorage("", name="auth_session")

    @rx.var
    def users(self) -> list[User]:
        """Get the list of users from local storage."""
        try:
            return json.loads(self.users_json)
        except json.JSONDecodeError as e:
            import logging

            logging.exception(f"Error decoding users_json: {e}")
            return []

    def _save_users(self, users: list[User]):
        """Save the list of users to local storage."""
        self.users_json = json.dumps(users)

    @rx.var
    def session(self) -> Optional[Session]:
        """Get the current session from local storage."""
        if not self.session_json:
            return None
        try:
            return json.loads(self.session_json)
        except json.JSONDecodeError as e:
            import logging

            logging.exception(f"Error decoding session_json: {e}")
            return None

    @rx.var
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.session is not None

    @rx.var
    def current_user_email(self) -> str:
        """Get the email of the currently logged-in user."""
        return self.session["email"] if self.session else ""

    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    @rx.event
    def register(self, form_data: dict):
        """Register a new user."""
        email = form_data.get("email", "").strip().lower()
        password = form_data.get("password", "")
        confirm_password = form_data.get("confirm_password", "")
        if not email or not password or (not confirm_password):
            return rx.toast.error("All fields are required.")
        if not re.match("[^@]+@[^@]+\\.[^@]+", email):
            return rx.toast.error("Invalid email format.")
        if password != confirm_password:
            return rx.toast.error("Passwords do not match.")
        if len(password) < 8:
            return rx.toast.error("Password must be at least 8 characters long.")
        if any((u["email"] == email for u in self.users)):
            return rx.toast.error("Email already registered.")
        password_hash = self._hash_password(password)
        new_user: User = {"email": email, "password_hash": password_hash}
        updated_users = self.users + [new_user]
        self._save_users(updated_users)
        yield rx.toast.success("Registration successful! Please log in.")
        return rx.redirect("/login")

    @rx.event
    def login(self, form_data: dict):
        """Log in a user."""
        email = form_data.get("email", "").strip().lower()
        password = form_data.get("password", "")
        if not email or not password:
            return rx.toast.error("Email and password are required.")
        user = next((u for u in self.users if u["email"] == email), None)
        password_hash = self._hash_password(password)
        if not user or user["password_hash"] != password_hash:
            return rx.toast.error("Invalid email or password.")
        self.session_json = json.dumps({"email": user["email"]})
        return rx.redirect("/")

    @rx.event
    def logout(self):
        """Log out the current user."""
        self.session_json = ""
        return rx.redirect("/login")

    @rx.event
    def check_auth(self):
        """Check if the user is authenticated and redirect if not."""
        if not self.is_authenticated:
            return rx.redirect("/login")