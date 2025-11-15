import reflex as rx

from app.state.login_state import LoginState

class LoginForm(rx.Component):
    """A component representing the login input form."""
    
    # Define a custom tag for the component
    @classmethod
    def get_component(cls) -> rx.Component:
        # We bind directly to the LoginState methods and variables
        return rx.vstack(
            rx.heading("Login", size="9"),
            
            # Username Input
            rx.input(
                placeholder="Username",
                on_change=LoginState.set_username,
                value=LoginState.username,
                size="3",
                width="100%",
            ),
            
            # Password Input
            rx.input(
                placeholder="Password",
                on_change=LoginState.set_password,
                value=LoginState.password,
                type_="password", 
                size="3",
                width="100%",
            ),
            
            # Error Message Display
            rx.cond(
                LoginState.error_message,
                rx.text(
                    LoginState.error_message,
                    color="red",
                    padding_bottom="1em"
                ),
            ),
            
            # Login Button 
            rx.button(
                "Log In",
                on_click=LoginState.handle_login,
                is_loading=LoginState.is_loading, # Uses the manual state var
                size="3",
                width="100%",
            ),
            
            align="center",
            padding="2em",
            border="1px solid #ccc",
            border_radius="10px",
            max_width="400px",
            width="90%",
            box_shadow="lg",
        )

# Instantiate the form component
login_form = LoginForm.get_component()