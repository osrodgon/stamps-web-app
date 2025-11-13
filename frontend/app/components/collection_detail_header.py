import reflex as rx
from app.states.collections_state import CollectionsState


def collection_detail_header() -> rx.Component:
    """Header for the collection detail page."""
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.a(
                    rx.icon("chevron-left", class_name="h-4 w-4"),
                    "Collections",
                    href="/",
                    class_name="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 transition-colors",
                ),
                rx.el.span("/", class_name="text-gray-300 mx-2"),
                rx.cond(
                    CollectionsState.current_collection,
                    rx.el.span(
                        CollectionsState.current_collection["name"],
                        class_name="font-semibold text-gray-800",
                    ),
                    rx.el.div(
                        class_name="bg-gray-200 h-4 w-32 rounded-md animate-pulse"
                    ),
                ),
                class_name="flex items-center text-sm",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "search",
                        class_name="h-5 w-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2",
                    ),
                    rx.el.input(
                        id="item_search_input",
                        placeholder="Search items...",
                        default_value=CollectionsState.item_search_query,
                        on_change=CollectionsState.set_item_search_query.debounce(300),
                        class_name="w-full max-w-xs pl-10 pr-4 py-2 rounded-md border border-gray-300 bg-white focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-all text-sm",
                    ),
                    class_name="relative",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4 mr-1.5"),
                    "Add Item",
                    on_click=CollectionsState.toggle_new_item_modal,
                    class_name="flex items-center px-4 py-2 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-600 active:scale-98 transition-all shadow-sm bg-gradient-to-br from-orange-400 to-orange-600",
                ),
                class_name="flex items-center gap-4",
            ),
            class_name="flex items-center justify-between",
        ),
        class_name="px-8 py-4 border-b border-gray-200 bg-white/80 backdrop-blur-md sticky top-0 z-40",
    )