import reflex as rx
import httpx # Use httpx for asynchronous HTTP requests

from app.state.abstract_state import AbstractState
from settings import BACKEND_URL

class LoginState(rx.State):
    """The state for the login page."""
    username: str = ""
    password: str = ""
    error_message: str = ""
    is_authenticated: bool = False
    is_loading: bool = False
    
    # Store the received token for later use (e.g., in other state methods)
    auth_token: str = "" 

    def set_username(self, username: str):
        """Update the username state variable."""
        self.username = username
        self.error_message = "" # Clear errors on new input

    def set_password(self, password: str):
        """Update the password state variable."""
        self.password = password
        self.error_message = "" # Clear errors on new input

    async def handle_login(self):
        """Handle the login form submission and call the Django API."""
        self.error_message = ""
        self.is_loading = True
        
        # 1. Prepare the credentials
        credentials = {
            "username": self.username,
            "password": self.password,
        }
        
        # 2. Make the API request
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{BACKEND_URL}/token/", json=credentials, timeout=5.0)
                
                # Check for successful response (e.g., 200 OK)
                if response.status_code == 200:
                    token_data = response.json()
                    # Assuming your Django backend returns a 'token' or 'access' field
                    self.auth_token = token_data.get("access", "") 
                    self.is_authenticated = True
                    # Navigate to the next page upon successful login
                    return rx.redirect("/collections") 
                else:
                    # Handle API errors (e.g., 401 Unauthorized)
                    error_data = response.json()
                    self.error_message = error_data.get("detail", "Invalid credentials or API error.")
                    self.is_authenticated = False
                    
        except httpx.ConnectError:
            self.error_message = "Could not connect to the API server."
        except Exception as e:
            self.error_message = f"An unexpected error occurred: {e}"
        finally:
            # Clear sensitive data in state after a failed attempt
            self.password = ""
            self.is_loading = False