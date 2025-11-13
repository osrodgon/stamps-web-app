import reflex as rx
from app.states.auth_state import AuthState


def auth_layout(title: str, *children) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("box", class_name="h-8 w-8 text-orange-500"),
                rx.el.h2(title, class_name="text-2xl font-bold text-gray-800"),
                class_name="flex items-center gap-3 justify-center",
            ),
            *children,
            class_name="w-full max-w-md bg-white p-8 rounded-xl shadow-sm border border-gray-200 space-y-6",
        ),
        class_name="flex min-h-screen items-center justify-center bg-gray-50 font-['Raleway'] p-4",
    )


def login_page() -> rx.Component:
    """The login page for the application."""
    return auth_layout(
        "Sign In",
        rx.el.form(
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Email Address",
                        html_for="email",
                        class_name="text-sm font-medium text-gray-700",
                    ),
                    rx.el.input(
                        id="email",
                        name="email",
                        type="email",
                        placeholder="you@example.com",
                        class_name="w-full px-3 py-2 rounded-md border border-gray-300 focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-shadow",
                        required=True,
                    ),
                    class_name="space-y-1",
                ),
                rx.el.div(
                    rx.el.label(
                        "Password",
                        html_for="password",
                        class_name="text-sm font-medium text-gray-700",
                    ),
                    rx.el.input(
                        id="password",
                        name="password",
                        type="password",
                        class_name="w-full px-3 py-2 rounded-md border border-gray-300 focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-shadow",
                        required=True,
                    ),
                    class_name="space-y-1",
                ),
                class_name="space-y-4",
            ),
            rx.el.button(
                "Sign In",
                type="submit",
                class_name="w-full mt-6 px-4 py-2 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-600 active:scale-98 transition-all shadow-sm bg-gradient-to-br from-orange-400 to-orange-600",
            ),
            on_submit=AuthState.login,
        ),
        rx.el.p(
            "Don't have an account? ",
            rx.el.a(
                "Sign Up",
                href="/register",
                class_name="font-semibold text-orange-500 hover:underline",
            ),
            class_name="text-center text-sm text-gray-600 pt-4 border-t border-gray-100",
        ),
    )