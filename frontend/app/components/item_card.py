import reflex as rx
from app.states.collections_state import Item, CollectionsState


def item_menu(item: Item) -> rx.Component:
    """A dropdown menu for item actions."""
    return rx.radix.dropdown_menu.root(
        rx.radix.dropdown_menu.trigger(
            rx.el.button(
                rx.icon("ellipsis", class_name="h-4 w-4"),
                class_name="p-1 rounded-full hover:bg-gray-200 transition-colors opacity-0 group-hover:opacity-100",
            )
        ),
        rx.radix.dropdown_menu.content(
            rx.radix.dropdown_menu.item(
                "Edit",
                on_click=lambda: CollectionsState.open_edit_item_modal(item),
                shortcut="E",
            ),
            rx.radix.dropdown_menu.separator(),
            rx.radix.dropdown_menu.item(
                "Delete",
                color="red",
                on_click=lambda: CollectionsState.open_delete_item_modal(item),
            ),
        ),
    )


def item_card(item: Item, **props) -> rx.Component:
    """A card that displays a single item."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("file-text", class_name="h-6 w-6 text-gray-400"),
                item_menu(item),
                class_name="flex items-center justify-between mb-3",
            ),
            rx.el.h3(
                item["name"], class_name="font-semibold text-gray-800 text-md truncate"
            ),
            rx.el.p(
                item["description"],
                class_name="text-gray-500 text-sm h-10 mt-1 overflow-hidden",
            ),
            rx.el.div(
                rx.foreach(
                    item["tags"],
                    lambda tag: rx.el.span(
                        tag,
                        class_name="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full",
                    ),
                ),
                class_name="flex flex-wrap gap-1 mt-3 h-6 overflow-hidden",
            ),
            class_name="p-4",
        ),
        class_name="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300 ease-in-out flex flex-col h-48 group",
        **props,
    )