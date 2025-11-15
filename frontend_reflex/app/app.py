import reflex as rx

from app.pages.login_page import login_page

app = rx.App()

# Add the login page, passing the function itself
app.add_page(login_page, route="/login")