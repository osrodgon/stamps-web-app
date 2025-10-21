import reflex as rx
from app.components.sidebar import sidebar
from app.components.stamp_view import stamp_detail_view, hamburger_menu
from app.state import CollectionState


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.cond(
                CollectionState.show_sidebar,
                rx.el.div(
                    on_click=CollectionState.toggle_sidebar,
                    class_name="fixed inset-0 bg-black/50 z-40 md:hidden",
                ),
            ),
            sidebar(),
            rx.el.div(
                stamp_detail_view(),
                class_name="flex-1 h-screen overflow-y-auto relative",
            ),
            hamburger_menu(),
            class_name="flex w-full h-screen",
        ),
        class_name="font-['JetBrains_Mono'] bg-white",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index)