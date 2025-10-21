import reflex as rx
from typing import TypedDict


class Stamp(TypedDict):
    name: str
    scott_number: str
    description: str
    image_url: str
    condition: str
    purchase_price: float


class Issue(TypedDict):
    name: str
    country: str
    stamps: list[Stamp]


class YearCollection(TypedDict):
    year: int
    issues: list[Issue]


class CollectionState(rx.State):
    collection: list[YearCollection] = [
        {
            "year": 2023,
            "issues": [
                {
                    "name": "Cosmic Wonders",
                    "country": "USA",
                    "stamps": [
                        {
                            "name": "Orion Nebula",
                            "scott_number": "5810",
                            "description": "A stunning depiction of the Orion Nebula.",
                            "image_url": "/placeholder.svg",
                            "condition": "Mint",
                            "purchase_price": 1.5,
                        },
                        {
                            "name": "Andromeda Galaxy",
                            "scott_number": "5811",
                            "description": "Features our galactic neighbor, Andromeda.",
                            "image_url": "/placeholder.svg",
                            "condition": "Used",
                            "purchase_price": 0.25,
                        },
                    ],
                },
                {
                    "name": "Deep Sea Creatures",
                    "country": "Japan",
                    "stamps": [
                        {
                            "name": "Giant Squid",
                            "scott_number": "JP-4501",
                            "description": "An elusive giant of the deep.",
                            "image_url": "/placeholder.svg",
                            "condition": "Mint",
                            "purchase_price": 2.1,
                        }
                    ],
                },
            ],
        },
        {
            "year": 2022,
            "issues": [
                {
                    "name": "National Parks Centennial",
                    "country": "USA",
                    "stamps": [
                        {
                            "name": "Yellowstone Geyser",
                            "scott_number": "5720",
                            "description": "Old Faithful in its full glory.",
                            "image_url": "/placeholder.svg",
                            "condition": "Mint",
                            "purchase_price": 0.95,
                        },
                        {
                            "name": "Grand Canyon",
                            "scott_number": "5721",
                            "description": "A view from the South Rim.",
                            "image_url": "/placeholder.svg",
                            "condition": "Mint",
                            "purchase_price": 0.95,
                        },
                        {
                            "name": "Zion Narrows",
                            "scott_number": "5722",
                            "description": "The famous hiking trail.",
                            "image_url": "/placeholder.svg",
                            "condition": "Used",
                            "purchase_price": 0.15,
                        },
                    ],
                }
            ],
        },
        {
            "year": 2021,
            "issues": [
                {
                    "name": "Legendary Cars",
                    "country": "Germany",
                    "stamps": [
                        {
                            "name": "Porsche 911",
                            "scott_number": "DE-3450",
                            "description": "The classic sports car.",
                            "image_url": "/placeholder.svg",
                            "condition": "Mint",
                            "purchase_price": 1.8,
                        }
                    ],
                }
            ],
        },
    ]
    selected_year: int | None = 2023
    selected_issue_idx: int | None = 0
    selected_stamp_idx: int | None = None
    show_settings_menu: bool = False
    show_sidebar: bool = True

    @rx.var
    def collection_sorted(self) -> list[YearCollection]:
        return sorted(self.collection, key=lambda c: c["year"], reverse=True)

    @rx.var
    def current_year_collection(self) -> YearCollection | None:
        if self.selected_year is None:
            return None
        for c in self.collection:
            if c["year"] == self.selected_year:
                return c
        return None

    @rx.var
    def current_issues(self) -> list[Issue]:
        return (
            self.current_year_collection["issues"]
            if self.current_year_collection
            else []
        )

    @rx.var
    def current_issue(self) -> Issue | None:
        if self.selected_issue_idx is not None and self.current_issues:
            if self.selected_issue_idx < len(self.current_issues):
                return self.current_issues[self.selected_issue_idx]
        return None

    @rx.var
    def current_stamps(self) -> list[Stamp]:
        return self.current_issue["stamps"] if self.current_issue else []

    @rx.var
    def selected_stamp(self) -> Stamp | None:
        if self.selected_stamp_idx is not None and self.current_stamps:
            if self.selected_stamp_idx < len(self.current_stamps):
                return self.current_stamps[self.selected_stamp_idx]
        return None

    @rx.event
    def toggle_year(self, year: int):
        if self.selected_year == year:
            self.selected_year = None
            self.selected_issue_idx = None
        else:
            self.selected_year = year
            self.selected_issue_idx = None

    @rx.event
    def select_issue(self, year: int, idx: int):
        self.selected_year = year
        self.selected_issue_idx = idx
        self.selected_stamp_idx = None

    @rx.event
    def select_stamp(self, idx: int):
        self.selected_stamp_idx = idx

    @rx.event
    def clear_stamp_selection(self):
        self.selected_stamp_idx = None

    @rx.event
    def toggle_settings_menu(self):
        self.show_settings_menu = not self.show_settings_menu

    @rx.event
    def toggle_sidebar(self):
        self.show_sidebar = not self.show_sidebar

    @rx.event
    def close_sidebar_if_mobile(self):
        if not self.show_sidebar:
            return
        self.show_sidebar = False