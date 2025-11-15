from app.components.forms.login_form import login_form
import reflex as rx

class LoginPage(rx.Component):
    """The login form component."""
    
    # Define a custom tag for the component (optional, but good practice)
    @classmethod
    def get_component(cls) -> rx.Component:
        return rx.center(
            login_form,
            width="100vw",
            height="100vh",
        )

# Instantiate the component for use in the app
login_page = LoginPage.get_component()