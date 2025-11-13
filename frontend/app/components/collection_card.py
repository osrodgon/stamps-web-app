import reflex as rx
from app.states.collections_state import Collection, CollectionsState


def card_menu(collection: Collection) -> rx.Component:
    """A dropdown menu for card actions."""
    return rx.radix.dropdown_menu.root(
        rx.radix.dropdown_menu.trigger(
            rx.el.button(
                rx.icon("ellipsis", class_name="h-4 w-4"),
                class_name="p-1 rounded-full hover:bg-gray-200 transition-colors",
                on_click=rx.stop_propagation,
            )
        ),
        rx.radix.dropdown_menu.content(
            rx.radix.dropdown_menu.item(
                "Edit",
                on_click=lambda: CollectionsState.open_edit_collection_modal(
                    collection
                ),
                shortcut="E",
            ),
            rx.radix.dropdown_menu.separator(),
            rx.radix.dropdown_menu.item(
                "Delete",
                color="red",
                on_click=lambda: CollectionsState.open_delete_collection_modal(
                    collection
                ),
            ),
        ),
    )


def collection_card(collection: Collection, **props) -> rx.Component:
    """A card that displays a single collection."""
    return rx.el.div(
        rx.el.div(
            class_name=rx.match(
                collection["color"],
                ("orange", "h-2 w-full rounded-t-lg bg-orange-500"),
                ("blue", "h-2 w-full rounded-t-lg bg-blue-500"),
                ("green", "h-2 w-full rounded-t-lg bg-green-500"),
                ("purple", "h-2 w-full rounded-t-lg bg-purple-500"),
                ("pink", "h-2 w-full rounded-t-lg bg-pink-500"),
                ("gray", "h-2 w-full rounded-t-lg bg-gray-500"),
                "h-2 w-full rounded-t-lg bg-gray-500",
            )
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    collection["name"],
                    class_name="font-semibold text-gray-800 text-lg truncate",
                ),
                card_menu(collection),
                class_name="flex items-center justify-between",
            ),
            rx.el.p(
                collection["description"], class_name="text-gray-500 text-sm h-10 mt-1"
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span("Items", class_name="text-xs text-gray-500"),
                    rx.el.span(
                        collection["item_count"],
                        class_name="text-sm font-semibold text-gray-700",
                    ),
                    class_name="flex flex-col",
                ),
                rx.el.div(
                    rx.el.span("Last updated", class_name="text-xs text-gray-500"),
                    rx.el.span(
                        rx.moment(collection["updated_at"], from_now=True),
                        class_name="text-sm font-semibold text-gray-700",
                    ),
                    class_name="flex flex-col text-right",
                ),
                class_name="mt-4 pt-4 border-t border-gray-100 flex justify-between items-center",
            ),
            class_name="p-4 flex flex-col justify-between h-full",
        ),
        class_name="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300 ease-in-out flex flex-col h-48 cursor-pointer",
        on_click=lambda: CollectionsState.go_to_collection(collection["id"]),
        **props,
    )