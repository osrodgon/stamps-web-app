import reflex as rx
from app.states.auth_state import AuthState
from app.pages.login_page import auth_layout


def register_page() -> rx.Component:
    """The registration page for the application."""
    return auth_layout(
        "Create Account",
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
                        placeholder="8+ characters",
                        class_name="w-full px-3 py-2 rounded-md border border-gray-300 focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-shadow",
                        required=True,
                    ),
                    class_name="space-y-1",
                ),
                rx.el.div(
                    rx.el.label(
                        "Confirm Password",
                        html_for="confirm_password",
                        class_name="text-sm font-medium text-gray-700",
                    ),
                    rx.el.input(
                        id="confirm_password",
                        name="confirm_password",
                        type="password",
                        class_name="w-full px-3 py-2 rounded-md border border-gray-300 focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-shadow",
                        required=True,
                    ),
                    class_name="space-y-1",
                ),
                class_name="space-y-4",
            ),
            rx.el.button(
                "Create Account",
                type="submit",
                class_name="w-full mt-6 px-4 py-2 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-600 active:scale-98 transition-all shadow-sm bg-gradient-to-br from-orange-400 to-orange-600",
            ),
            on_submit=AuthState.register,
        ),
        rx.el.p(
            "Already have an account? ",
            rx.el.a(
                "Sign In",
                href="/login",
                class_name="font-semibold text-orange-500 hover:underline",
            ),
            class_name="text-center text-sm text-gray-600 pt-4 border-t border-gray-100",
        ),
    )