import reflex as rx
from app.states.collections_state import CollectionsState
from app.states.auth_state import AuthState


def user_menu() -> rx.Component:
    return rx.radix.dropdown_menu.root(
        rx.radix.dropdown_menu.trigger(
            rx.el.button(
                rx.image(
                    src=f"https://api.dicebear.com/9.x/notionists-neutral/svg?seed={AuthState.current_user_email}",
                    class_name="h-8 w-8 rounded-full",
                ),
                class_name="rounded-full focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2",
            )
        ),
        rx.radix.dropdown_menu.content(
            rx.el.div(
                AuthState.current_user_email,
                class_name="px-2 py-1.5 text-sm font-normal text-gray-500",
            ),
            rx.radix.dropdown_menu.separator(),
            rx.radix.dropdown_menu.item("Logout", on_click=AuthState.logout),
        ),
    )


def header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.icon("box", class_name="h-7 w-7 text-orange-500"),
                rx.el.div(
                    rx.el.span(
                        "Collections", class_name="text-lg font-semibold text-gray-800"
                    ),
                    rx.el.span(
                        f"Welcome, {AuthState.current_user_email}",
                        class_name="text-xs text-gray-500",
                    ),
                    class_name="flex flex-col leading-tight",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "search",
                        class_name="h-5 w-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2",
                    ),
                    rx.el.input(
                        id="collection_search_input",
                        placeholder="Search collections...",
                        default_value=CollectionsState.search_query,
                        on_change=CollectionsState.set_search_query.debounce(300),
                        class_name="w-full max-w-sm pl-10 pr-10 py-2 rounded-md border border-gray-300 bg-white focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-all text-sm",
                    ),
                    rx.el.kbd(
                        "⌘K",
                        class_name="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded",
                    ),
                    class_name="relative",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4 mr-1.5"),
                    "New Collection",
                    rx.el.kbd(
                        "N",
                        class_name="ml-4 text-xs text-orange-200 bg-orange-600/50 px-1.5 py-0.5 rounded",
                    ),
                    on_click=CollectionsState.toggle_new_collection_modal,
                    class_name="flex items-center px-4 py-2 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-600 active:scale-98 transition-all shadow-sm bg-gradient-to-br from-orange-400 to-orange-600",
                ),
                user_menu(),
                class_name="flex items-center gap-4",
            ),
            class_name="flex items-center justify-between",
        ),
        class_name="px-8 py-4 border-b border-gray-200 bg-white/80 backdrop-blur-md sticky top-0 z-40",
    )