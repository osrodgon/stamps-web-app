import reflex as rx
from app.state import CollectionState, Issue, YearCollection


def issue_button(issue: Issue, year: int, index: int) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.el.p(issue["name"], class_name="font-medium"),
                rx.el.span(issue["country"], class_name="text-xs"),
                class_name="flex flex-col items-start",
            ),
            rx.el.span(
                issue["stamps"].length().to_string(),
                class_name="text-xs font-semibold px-1.5 py-0.5 rounded-full",
            ),
            class_name="flex justify-between items-center w-full",
        ),
        on_click=[
            lambda: CollectionState.select_issue(year, index),
            CollectionState.close_sidebar_if_mobile,
        ],
        class_name=rx.cond(
            (CollectionState.selected_year == year)
            & (CollectionState.selected_issue_idx == index),
            "w-full text-left pl-10 pr-4 py-2 rounded-lg text-teal-800 bg-teal-100/50",
            "w-full text-left pl-10 pr-4 py-2 rounded-lg text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900",
        ),
        transition="all 150ms ease-in-out",
    )


def year_group(year_collection: YearCollection) -> rx.Component:
    is_selected = CollectionState.selected_year == year_collection["year"]
    return rx.el.div(
        rx.el.button(
            rx.el.div(
                year_collection["year"].to_string(), class_name="text-sm font-semibold"
            ),
            rx.icon(
                tag=rx.cond(is_selected, "chevron-down", "chevron-right"),
                size=18,
                class_name="text-neutral-500",
            ),
            on_click=lambda: CollectionState.toggle_year(year_collection["year"]),
            class_name="w-full flex justify-between items-center px-4 py-1 rounded-lg text-neutral-600 hover:bg-neutral-100",
        ),
        rx.cond(
            is_selected,
            rx.el.div(
                rx.foreach(
                    year_collection["issues"],
                    lambda issue, index: issue_button(
                        issue, year_collection["year"], index
                    ),
                ),
                class_name="flex flex-col pt-1",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col",
    )


def nav_item(
    icon: str, text: str, on_click: rx.event.EventSpec | None = None
) -> rx.Component:
    return rx.el.button(
        rx.icon(
            tag=icon,
            size=20,
            class_name="text-neutral-500 group-hover:text-neutral-700",
        ),
        rx.el.span(text, class_name="font-medium"),
        class_name="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 group",
        on_click=on_click,
    )


def sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("box", class_name="text-teal-600", size=24),
                    rx.el.h1(
                        "StampBook", class_name="text-xl font-bold text-neutral-800"
                    ),
                    class_name="flex items-center gap-3",
                ),
                class_name="p-4 mb-2",
            ),
            rx.el.div(
                rx.el.h2(
                    "Collection",
                    class_name="px-4 text-sm font-semibold text-neutral-500 mb-2",
                ),
                rx.el.div(
                    rx.foreach(CollectionState.collection_sorted, year_group),
                    class_name="flex flex-col gap-2 p-2 overflow-y-auto",
                ),
                class_name="flex-grow flex flex-col",
            ),
            class_name="flex-grow flex flex-col overflow-hidden",
        ),
        rx.el.div(
            rx.cond(
                CollectionState.show_settings_menu,
                rx.el.div(
                    nav_item("sliders-horizontal", "Configure"),
                    nav_item("pencil", "Edit Mode"),
                    nav_item("log-out", "Logout"),
                    class_name="flex flex-col gap-1 p-2",
                ),
                rx.fragment(),
            ),
            rx.el.button(
                rx.el.div(
                    rx.image(
                        src=f"https://api.dicebear.com/9.x/notionists/svg?seed=user_email",
                        class_name="size-8 rounded-full",
                    ),
                    rx.el.div(
                        rx.el.p("User Name", class_name="font-semibold text-sm"),
                        rx.el.p(
                            "user@example.com", class_name="text-xs text-neutral-500"
                        ),
                        class_name="flex flex-col items-start",
                    ),
                    class_name="flex items-center gap-3",
                ),
                rx.icon(
                    tag=rx.cond(
                        CollectionState.show_settings_menu, "chevron-down", "chevron-up"
                    ),
                    size=20,
                    class_name="text-neutral-500",
                ),
                class_name="w-full flex items-center justify-between p-3 rounded-lg hover:bg-neutral-100",
                on_click=CollectionState.toggle_settings_menu,
            ),
            class_name="p-2 border-t border-neutral-200",
        ),
        class_name=rx.cond(
            CollectionState.show_sidebar,
            "w-80 h-screen flex flex-col bg-white border-r border-neutral-200 fixed top-0 left-0 z-50 transform translate-x-0 transition-transform duration-300 ease-in-out md:relative md:translate-x-0",
            "w-80 h-screen flex flex-col bg-white border-r border-neutral-200 fixed top-0 left-0 z-50 transform -translate-x-full transition-transform duration-300 ease-in-out md:relative md:w-0 md:border-none md:translate-x-0",
        ),
    )