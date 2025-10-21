import reflex as rx
from app.state import CollectionState, Stamp


def hamburger_menu() -> rx.Component:
    return rx.el.button(
        rx.icon("menu", size=24),
        on_click=CollectionState.toggle_sidebar,
        class_name="fixed top-4 left-4 z-[51] p-2 rounded-md text-neutral-600 hover:bg-neutral-100 bg-white/50 backdrop-blur-sm",
    )


def stamp_grid_item(stamp: Stamp, index: int) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.image(
                src=stamp["image_url"],
                class_name="w-full h-32 object-cover rounded-t-lg",
            ),
            rx.el.div(
                rx.el.p(
                    stamp["name"],
                    class_name="font-semibold text-sm text-neutral-700 truncate",
                ),
                class_name="p-3",
            ),
            class_name="bg-white rounded-lg border border-neutral-200 hover:border-teal-500 hover:shadow-md transition-all duration-150 overflow-hidden",
        ),
        on_click=lambda: CollectionState.select_stamp(index),
    )


def stamp_detail_view() -> rx.Component:
    return rx.el.div(
        rx.cond(
            CollectionState.selected_stamp,
            rx.el.div(
                rx.el.div(
                    rx.el.button(
                        rx.icon("arrow-left", size=20),
                        on_click=CollectionState.clear_stamp_selection,
                        class_name="absolute top-6 left-6 p-2 rounded-full hover:bg-neutral-100 transition-colors",
                    ),
                    rx.el.div(
                        rx.image(
                            src=CollectionState.selected_stamp["image_url"],
                            class_name="w-full max-w-md h-auto rounded-xl shadow-lg border border-neutral-200",
                        ),
                        rx.el.div(
                            rx.el.h2(
                                CollectionState.selected_stamp["name"],
                                class_name="text-3xl font-bold text-neutral-900",
                            ),
                            rx.el.span(
                                f"Scott #{CollectionState.selected_stamp['scott_number']}",
                                class_name="font-mono text-sm text-neutral-500 bg-neutral-100 px-2 py-1 rounded",
                            ),
                            rx.el.p(
                                CollectionState.selected_stamp["description"],
                                class_name="text-neutral-700 mt-4 max-w-prose leading-relaxed",
                            ),
                            rx.el.div(
                                rx.el.div(
                                    rx.el.span(
                                        "Condition",
                                        class_name="text-sm font-medium text-neutral-500",
                                    ),
                                    rx.el.span(
                                        CollectionState.selected_stamp["condition"],
                                        class_name="text-base font-semibold text-neutral-800",
                                    ),
                                    class_name="flex flex-col",
                                ),
                                rx.el.div(
                                    rx.el.span(
                                        "Price",
                                        class_name="text-sm font-medium text-neutral-500",
                                    ),
                                    rx.el.span(
                                        f"${CollectionState.selected_stamp['purchase_price']:.2f}",
                                        class_name="text-base font-semibold text-teal-600",
                                    ),
                                    class_name="flex flex-col",
                                ),
                                class_name="flex gap-8 mt-6",
                            ),
                            class_name="flex flex-col gap-2 py-8",
                        ),
                        class_name="grid md:grid-cols-2 gap-12 items-start",
                    ),
                    class_name="p-8 md:p-12 relative w-full",
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        "Stamps in ",
                        rx.el.span(
                            rx.cond(
                                CollectionState.current_issue,
                                CollectionState.current_issue["name"],
                                "",
                            ),
                            class_name="text-teal-600",
                        ),
                        class_name="text-2xl font-bold text-neutral-800",
                    ),
                    rx.el.button(
                        rx.icon("plus", size=16),
                        "Add Stamp",
                        class_name="bg-gradient-to-r from-teal-500 to-cyan-500 text-white flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium hover:from-teal-600 hover:to-cyan-600 transition-all shadow-sm",
                    ),
                    class_name="flex justify-between items-center p-6 border-b border-neutral-200",
                ),
                rx.cond(
                    CollectionState.current_stamps.length() > 0,
                    rx.el.div(
                        rx.foreach(CollectionState.current_stamps, stamp_grid_item),
                        class_name="p-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 overflow-y-auto",
                    ),
                    rx.el.div(
                        rx.icon("archive", size=32, class_name="text-neutral-400 mb-4"),
                        rx.el.span(
                            "No stamps in this issue.", class_name="text-neutral-500"
                        ),
                        rx.el.span(
                            "Click 'Add Stamp' to get started.",
                            class_name="text-sm text-neutral-400 mt-1",
                        ),
                        class_name="h-full flex flex-col items-center justify-center text-center p-6",
                    ),
                ),
                class_name="h-full flex flex-col",
            ),
        )
    )