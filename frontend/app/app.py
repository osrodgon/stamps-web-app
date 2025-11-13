import reflex as rx
from app.states.collections_state import CollectionsState
from app.states.auth_state import AuthState
from app.components.header import header
from app.components.collection_card import collection_card
from app.components.modals import (
    new_collection_modal,
    edit_collection_modal,
    delete_collection_confirmation_modal,
    new_item_modal,
    edit_item_modal,
    delete_item_confirmation_modal,
)
from app.components.collection_detail_header import collection_detail_header
from app.components.item_card import item_card
from app.pages.login_page import login_page
from app.pages.register_page import register_page


def empty_state() -> rx.Component:
    """The component to display when there are no collections."""
    return rx.el.div(
        rx.icon("folder-open", class_name="h-16 w-16 text-gray-300"),
        rx.el.h2(
            "No Collections Yet", class_name="text-xl font-semibold text-gray-700 mt-4"
        ),
        rx.el.p(
            "Get started by creating your first collection.",
            class_name="text-gray-500 mt-1",
        ),
        rx.el.button(
            "Create Collection",
            on_click=CollectionsState.toggle_new_collection_modal,
            class_name="mt-6 px-4 py-2 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-600 active:scale-98 transition-all shadow-sm bg-gradient-to-br from-orange-400 to-orange-600",
        ),
        class_name="flex flex-col items-center justify-center text-center p-12 bg-gray-50 rounded-xl border border-dashed border-gray-300",
    )


def collections_grid() -> rx.Component:
    """The grid of all collections."""
    return rx.el.div(
        rx.foreach(
            CollectionsState.filtered_collections,
            lambda collection: collection_card(collection, key=collection["id"]),
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6",
    )


def global_hotkeys() -> rx.Component:
    """A component to handle global keyboard shortcuts."""
    return rx.window_event_listener(
        on_key_down=CollectionsState.handle_key_down, event="keydown"
    )


def index() -> rx.Component:
    print("Here")
    return rx.el.div(
        header(),
        rx.el.main(
            rx.el.div(
                rx.cond(
                    CollectionsState.collections_exist,
                    collections_grid(),
                    empty_state(),
                ),
                class_name="p-8 max-w-screen-xl mx-auto",
            )
        ),
        new_collection_modal(),
        edit_collection_modal(),
        delete_collection_confirmation_modal(),
        global_hotkeys(),
        class_name="font-['Raleway'] bg-gray-50 min-h-screen text-gray-800",
    )


def item_empty_state() -> rx.Component:
    return rx.el.div(
        rx.icon("package", class_name="h-16 w-16 text-gray-300"),
        rx.el.h2(
            "No Items in this Collection",
            class_name="text-xl font-semibold text-gray-700 mt-4",
        ),
        rx.el.p(
            "Add items to this collection to see them here.",
            class_name="text-gray-500 mt-1",
        ),
        rx.el.button(
            "Add Item",
            on_click=CollectionsState.toggle_new_item_modal,
            class_name="mt-6 px-4 py-2 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-600 active:scale-98 transition-all shadow-sm bg-gradient-to-br from-orange-400 to-orange-600",
        ),
        class_name="flex flex-col items-center justify-center text-center p-12 bg-gray-50 rounded-xl border border-dashed border-gray-300 mt-8",
    )


def items_grid() -> rx.Component:
    return rx.el.div(
        rx.foreach(
            CollectionsState.items_in_current_collection,
            lambda item: item_card(item, key=item["id"]),
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mt-8",
    )


def collection_detail() -> rx.Component:
    """The page for viewing a single collection."""
    return rx.el.div(
        collection_detail_header(),
        rx.el.main(
            rx.el.div(
                rx.cond(
                    CollectionsState.items_in_current_collection.length() > 0,
                    items_grid(),
                    item_empty_state(),
                ),
                class_name="p-8 max-w-screen-xl mx-auto",
            )
        ),
        new_item_modal(),
        edit_item_modal(),
        delete_item_confirmation_modal(),
        global_hotkeys(),
        class_name="font-['Raleway'] bg-gray-50 min-h-screen text-gray-800",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(login_page, route="/login")
app.add_page(register_page, route="/register")
app.add_page(index, route="/", on_load=AuthState.check_auth)
app.add_page(
    collection_detail,
    route="/collections/[collection_id]",
    on_load=[AuthState.check_auth, CollectionsState.on_detail_load],
)