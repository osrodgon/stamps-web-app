import reflex as rx
from app.states.collections_state import CollectionsState


def color_selector(color: str) -> rx.Component:
    """Component for a single color option in the form."""
    return rx.el.button(
        rx.cond(
            CollectionsState.new_collection_color == color,
            rx.icon("check", class_name="h-5 w-5 text-white"),
            None,
        ),
        on_click=lambda: CollectionsState.set_new_collection_color(color),
        class_name=rx.match(
            color,
            (
                "orange",
                "h-8 w-8 rounded-full transition-all duration-200 flex items-center justify-center bg-orange-500 hover:bg-orange-600",
            ),
            (
                "blue",
                "h-8 w-8 rounded-full transition-all duration-200 flex items-center justify-center bg-blue-500 hover:bg-blue-600",
            ),
            (
                "green",
                "h-8 w-8 rounded-full transition-all duration-200 flex items-center justify-center bg-green-500 hover:bg-green-600",
            ),
            (
                "purple",
                "h-8 w-8 rounded-full transition-all duration-200 flex items-center justify-center bg-purple-500 hover:bg-purple-600",
            ),
            (
                "pink",
                "h-8 w-8 rounded-full transition-all duration-200 flex items-center justify-center bg-pink-500 hover:bg-pink-600",
            ),
            (
                "gray",
                "h-8 w-8 rounded-full transition-all duration-200 flex items-center justify-center bg-gray-500 hover:bg-gray-600",
            ),
            "h-8 w-8 rounded-full transition-all duration-200 flex items-center justify-center bg-gray-400",
        ),
        type="button",
    )


def collection_form(submit_handler, button_text: str) -> rx.Component:
    """A reusable form for creating/editing a collection."""
    return rx.el.form(
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Collection Name",
                    html_for="collection_name",
                    class_name="text-sm font-medium text-gray-700",
                ),
                rx.el.input(
                    id="collection_name",
                    name="name",
                    placeholder="e.g. Brand Assets",
                    key=CollectionsState.new_collection_name,
                    default_value=CollectionsState.new_collection_name,
                    class_name="w-full px-3 py-2 rounded-md border border-gray-300 focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-shadow",
                ),
                class_name="space-y-1",
            ),
            rx.el.div(
                rx.el.label(
                    "Description (Optional)",
                    html_for="collection_desc",
                    class_name="text-sm font-medium text-gray-700",
                ),
                rx.el.textarea(
                    id="collection_desc",
                    name="description",
                    placeholder="A brief description of what this collection contains.",
                    key=CollectionsState.new_collection_description,
                    default_value=CollectionsState.new_collection_description,
                    class_name="w-full px-3 py-2 rounded-md border border-gray-300 h-24 resize-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-shadow",
                ),
                class_name="space-y-1",
            ),
            rx.el.div(
                rx.el.label("Color", class_name="text-sm font-medium text-gray-700"),
                rx.el.div(
                    rx.foreach(CollectionsState.preset_colors, color_selector),
                    class_name="flex items-center gap-3",
                ),
                class_name="space-y-2",
            ),
            class_name="py-6 space-y-6",
        ),
        rx.el.div(
            rx.radix.primitives.dialog.close(
                rx.el.button(
                    "Cancel",
                    class_name="px-4 py-2 rounded-md border border-gray-300 bg-white text-sm font-semibold text-gray-700 hover:bg-gray-50 active:scale-98 transition-all",
                    type="button",
                )
            ),
            rx.el.button(
                button_text,
                class_name="px-4 py-2 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-600 active:scale-98 transition-all shadow-sm bg-gradient-to-br from-orange-400 to-orange-600",
                type="submit",
            ),
            class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
        ),
        on_submit=submit_handler,
        reset_on_submit=True,
    )


def new_collection_modal() -> rx.Component:
    """Modal for creating a new collection."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                "New Collection", class_name="text-xl font-semibold text-gray-900"
            ),
            collection_form(CollectionsState.handle_create_submit, "Create Collection"),
            rx.radix.primitives.dialog.close(
                rx.el.button(
                    rx.icon("x", class_name="h-5 w-5"),
                    class_name="p-1 rounded-full hover:bg-gray-100 transition-colors absolute top-3 right-3",
                    type="button",
                )
            ),
            class_name="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 relative",
        ),
        open=CollectionsState.is_new_collection_modal_open,
        on_open_change=CollectionsState.toggle_new_collection_modal,
    )


def edit_collection_modal() -> rx.Component:
    """Modal for editing an existing collection."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                "Edit Collection", class_name="text-xl font-semibold text-gray-900"
            ),
            collection_form(CollectionsState.handle_edit_submit, "Save Changes"),
            rx.radix.primitives.dialog.close(
                rx.el.button(
                    rx.icon("x", class_name="h-5 w-5"),
                    class_name="p-1 rounded-full hover:bg-gray-100 transition-colors absolute top-3 right-3",
                    type="button",
                )
            ),
            class_name="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 relative",
        ),
        open=CollectionsState.is_edit_collection_modal_open,
        on_open_change=CollectionsState.close_edit_collection_modal,
    )


def delete_collection_confirmation_modal() -> rx.Component:
    """Modal to confirm collection deletion."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                "Delete Collection", class_name="text-xl font-semibold text-gray-900"
            ),
            rx.el.div(
                rx.el.p(
                    "Are you sure you want to delete this collection and all its items? This action cannot be undone.",
                    class_name="text-gray-600 text-sm py-6",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=CollectionsState.close_delete_collection_modal,
                        class_name="px-4 py-2 rounded-md border border-gray-300 bg-white text-sm font-semibold text-gray-700 hover:bg-gray-50 active:scale-98 transition-all",
                        type="button",
                    ),
                    rx.el.button(
                        "Delete",
                        on_click=CollectionsState.delete_collection,
                        class_name="px-4 py-2 rounded-md bg-red-600 text-white text-sm font-semibold hover:bg-red-700 active:scale-98 transition-all",
                        type="button",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
            ),
            rx.radix.primitives.dialog.close(
                rx.el.button(
                    rx.icon("x", class_name="h-5 w-5"),
                    class_name="p-1 rounded-full hover:bg-gray-100 transition-colors absolute top-3 right-3",
                    type="button",
                )
            ),
            class_name="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 relative",
        ),
        open=CollectionsState.is_delete_collection_modal_open,
        on_open_change=CollectionsState.close_delete_collection_modal,
    )


def item_form(submit_handler, item: rx.Var[dict], button_text: str) -> rx.Component:
    """A reusable form for creating/editing an item."""
    return rx.el.form(
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Item Name",
                    html_for="item_name",
                    class_name="text-sm font-medium text-gray-700",
                ),
                rx.el.input(
                    id="item_name",
                    name="name",
                    placeholder="e.g. Primary Logo",
                    default_value=rx.cond(item, item["name"], ""),
                    key=CollectionsState.editing_item.to_string(),
                    class_name="w-full px-3 py-2 rounded-md border border-gray-300 focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-shadow",
                ),
                class_name="space-y-1",
            ),
            rx.el.div(
                rx.el.label(
                    "Description (Optional)",
                    html_for="item_desc",
                    class_name="text-sm font-medium text-gray-700",
                ),
                rx.el.textarea(
                    id="item_desc",
                    name="description",
                    placeholder="A brief description of this item.",
                    default_value=rx.cond(item, item["description"], ""),
                    key=CollectionsState.editing_item.to_string(),
                    class_name="w-full px-3 py-2 rounded-md border border-gray-300 h-24 resize-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-shadow",
                ),
                class_name="space-y-1",
            ),
            rx.el.div(
                rx.el.label(
                    "Tags (comma-separated)",
                    html_for="item_tags",
                    class_name="text-sm font-medium text-gray-700",
                ),
                rx.el.input(
                    id="item_tags",
                    name="tags",
                    placeholder="logo, png, primary",
                    default_value=rx.cond(item, item["tags"].join(", "), ""),
                    key=CollectionsState.editing_item.to_string(),
                    class_name="w-full px-3 py-2 rounded-md border border-gray-300 focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-shadow",
                ),
                class_name="space-y-1",
            ),
            class_name="py-6 space-y-6",
        ),
        rx.el.div(
            rx.radix.primitives.dialog.close(
                rx.el.button(
                    "Cancel",
                    class_name="px-4 py-2 rounded-md border border-gray-300 bg-white text-sm font-semibold text-gray-700 hover:bg-gray-50 active:scale-98 transition-all",
                    type="button",
                )
            ),
            rx.el.button(
                button_text,
                class_name="px-4 py-2 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-600 active:scale-98 transition-all shadow-sm bg-gradient-to-br from-orange-400 to-orange-600",
                type="submit",
            ),
            class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
        ),
        on_submit=submit_handler,
        reset_on_submit=True,
    )


def new_item_modal() -> rx.Component:
    """Modal for creating a new item."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                "New Item", class_name="text-xl font-semibold text-gray-900"
            ),
            item_form(
                CollectionsState.handle_create_item_submit,
                CollectionsState.editing_item,
                "Create Item",
            ),
            rx.radix.primitives.dialog.close(
                rx.el.button(
                    rx.icon("x", class_name="h-5 w-5"),
                    class_name="p-1 rounded-full hover:bg-gray-100 transition-colors absolute top-3 right-3",
                    type="button",
                )
            ),
            class_name="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 relative",
        ),
        open=CollectionsState.is_new_item_modal_open,
        on_open_change=CollectionsState.toggle_new_item_modal,
    )


def edit_item_modal() -> rx.Component:
    """Modal for editing an existing item."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                "Edit Item", class_name="text-xl font-semibold text-gray-900"
            ),
            rx.cond(
                CollectionsState.editing_item,
                item_form(
                    CollectionsState.handle_edit_item_submit,
                    CollectionsState.editing_item,
                    "Save Changes",
                ),
                rx.el.div("Loading..."),
            ),
            rx.radix.primitives.dialog.close(
                rx.el.button(
                    rx.icon("x", class_name="h-5 w-5"),
                    class_name="p-1 rounded-full hover:bg-gray-100 transition-colors absolute top-3 right-3",
                    type="button",
                )
            ),
            class_name="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 relative",
        ),
        open=CollectionsState.is_edit_item_modal_open,
        on_open_change=CollectionsState.close_edit_item_modal,
    )


def delete_item_confirmation_modal() -> rx.Component:
    """Modal to confirm item deletion."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                "Delete Item", class_name="text-xl font-semibold text-gray-900"
            ),
            rx.el.div(
                rx.el.p(
                    "Are you sure you want to delete this item? This action cannot be undone.",
                    class_name="text-gray-600 text-sm py-6",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=CollectionsState.close_delete_item_modal,
                        class_name="px-4 py-2 rounded-md border border-gray-300 bg-white text-sm font-semibold text-gray-700 hover:bg-gray-50 active:scale-98 transition-all",
                        type="button",
                    ),
                    rx.el.button(
                        "Delete",
                        on_click=CollectionsState.delete_item,
                        class_name="px-4 py-2 rounded-md bg-red-600 text-white text-sm font-semibold hover:bg-red-700 active:scale-98 transition-all",
                        type="button",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
            ),
            rx.radix.primitives.dialog.close(
                rx.el.button(
                    rx.icon("x", class_name="h-5 w-5"),
                    class_name="p-1 rounded-full hover:bg-gray-100 transition-colors absolute top-3 right-3",
                    type="button",
                )
            ),
            class_name="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 relative",
        ),
        open=CollectionsState.is_delete_item_modal_open,
        on_open_change=CollectionsState.close_delete_item_modal,
    )