import reflex as rx
from typing import TypedDict, Literal, Optional
import uuid
import json
import logging
from datetime import datetime, timezone

Color = Literal["orange", "blue", "green", "purple", "pink", "gray"]


class Item(TypedDict):
    id: str
    name: str
    description: str
    tags: list[str]
    collection_id: str
    created_at: str
    updated_at: str


class Collection(TypedDict):
    id: str
    name: str
    description: str
    color: Color
    item_count: int
    updated_at: str


class CollectionsState(rx.State):
    """Manages the state for collections."""

    _collections_json: str = rx.LocalStorage("{}", name="collections")
    _items_json: str = rx.LocalStorage("{}", name="items")
    search_query: str = ""
    is_new_collection_modal_open: bool = False
    is_edit_collection_modal_open: bool = False
    is_delete_collection_modal_open: bool = False
    is_new_item_modal_open: bool = False
    is_edit_item_modal_open: bool = False
    is_delete_item_modal_open: bool = False
    editing_collection: Optional[Collection] = None
    deleting_collection_id: Optional[str] = None
    editing_item: Optional[Item] = None
    deleting_item_id: Optional[str] = None
    new_collection_name: str = ""
    new_collection_description: str = ""
    new_collection_color: Color = "orange"
    preset_colors: list[Color] = ["orange", "blue", "green", "purple", "pink", "gray"]
    item_search_query: str = ""

    @rx.var
    async def current_user_email(self) -> str:
        """The email of the currently logged-in user."""
        from app.states.auth_state import AuthState

        auth_state = await self.get_state(AuthState)
        return auth_state.current_user_email

    @rx.var
    def all_collections(self) -> dict[str, list[Collection]]:
        """All collections for all users."""
        try:
            return json.loads(self._collections_json) if self._collections_json else {}
        except json.JSONDecodeError as e:
            logging.exception(f"Error decoding _collections_json: {e}")
            return {}

    @rx.var
    async def collections(self) -> list[Collection]:
        """The list of collections for the current user."""
        from app.states.auth_state import AuthState

        auth_state = await self.get_state(AuthState)
        if not self.is_hydrated or not auth_state.is_authenticated:
            return []
        user_email = await self.get_value(auth_state.current_user_email)
        return self.all_collections.get(user_email, [])

    async def _save_collections(self, collections: list[Collection]):
        """Helper to save collections for the current user to local storage."""
        from app.states.auth_state import AuthState

        auth_state = await self.get_state(AuthState)
        if not auth_state.is_authenticated:
            return
        user_email = auth_state.current_user_email
        all_collections = self.all_collections
        all_collections[user_email] = collections
        self._collections_json = json.dumps(all_collections)

    @rx.var
    def all_items(self) -> dict[str, list[Item]]:
        """All items for all users."""
        try:
            return json.loads(self._items_json) if self._items_json else {}
        except json.JSONDecodeError as e:
            logging.exception(f"Error decoding _items_json: {e}")
            return {}

    @rx.var
    async def items(self) -> list[Item]:
        """The list of items for the current user."""
        from app.states.auth_state import AuthState

        auth_state = await self.get_state(AuthState)
        if not self.is_hydrated or not auth_state.is_authenticated:
            return []
        user_email = await self.get_value(auth_state.current_user_email)
        return self.all_items.get(user_email, [])

    async def _save_items(self, items: list[Item]):
        """Helper to save items for the current user to local storage."""
        from app.states.auth_state import AuthState

        auth_state = await self.get_state(AuthState)
        if not auth_state.is_authenticated:
            return
        user_email = auth_state.current_user_email
        all_items = self.all_items
        all_items[user_email] = items
        self._items_json = json.dumps(all_items)

    @rx.var
    async def filtered_collections(self) -> list[Collection]:
        """A list of collections filtered by the search query."""
        collections = await self.collections
        if not self.search_query.strip():
            return collections
        query = self.search_query.lower()
        return [
            c
            for c in collections
            if query in c["name"].lower() or query in c["description"].lower()
        ]

    @rx.var
    async def items_in_current_collection(self) -> list[Item]:
        """Get items for the currently viewed collection."""
        if not self.current_collection:
            return []
        collection_id = self.current_collection["id"]
        items = await self.items
        filtered_items = [i for i in items if i["collection_id"] == collection_id]
        if not self.item_search_query.strip():
            return filtered_items
        query = self.item_search_query.lower()
        return [
            i
            for i in filtered_items
            if query in i["name"].lower()
            or query in i["description"].lower()
            or any((query in tag.lower() for tag in i["tags"]))
        ]

    @rx.var
    async def collections_exist(self) -> bool:
        collections = await self.collections
        return len(collections) > 0

    def _reset_collection_form(self):
        """Helper to reset collection form fields."""
        self.new_collection_name = ""
        self.new_collection_description = ""
        self.new_collection_color = "orange"
        self.editing_collection = None

    def _reset_item_form(self):
        """Helper to reset item form fields."""
        self.editing_item = None

    @rx.event
    def set_search_query(self, query: str):
        """Set the search query."""
        self.search_query = query

    @rx.event
    def toggle_new_collection_modal(self):
        """Toggle the visibility of the new collection modal."""
        self.is_new_collection_modal_open = not self.is_new_collection_modal_open
        if not self.is_new_collection_modal_open:
            self._reset_collection_form()

    @rx.event
    def open_edit_collection_modal(self, collection: Collection):
        """Open the edit modal and populate it with collection data."""
        self.editing_collection = collection
        self.new_collection_name = collection["name"]
        self.new_collection_description = collection["description"]
        self.new_collection_color = collection["color"]
        self.is_edit_collection_modal_open = True

    @rx.event
    def close_edit_collection_modal(self):
        """Close the edit modal."""
        self.is_edit_collection_modal_open = False
        self._reset_collection_form()

    @rx.event
    def open_delete_collection_modal(self, collection: Collection):
        """Open the delete confirmation modal."""
        self.deleting_collection_id = collection["id"]
        self.is_delete_collection_modal_open = True

    @rx.event
    def close_delete_collection_modal(self):
        """Close the delete confirmation modal."""
        self.is_delete_collection_modal_open = False
        self.deleting_collection_id = None

    @rx.event
    def set_new_collection_color(self, color: Color):
        """Set the color for the new collection."""
        self.new_collection_color = color

    @rx.event
    async def handle_create_submit(self, form_data: dict):
        """Handle the form submission to create a new collection."""
        name = form_data.get("name", "").strip()
        if not name:
            return rx.toast.error("Collection name cannot be empty.")
        now = datetime.now(timezone.utc).isoformat()
        new_collection: Collection = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": form_data.get("description", ""),
            "color": self.new_collection_color,
            "item_count": 0,
            "updated_at": now,
        }
        current_collections = await self.collections
        current_collections.insert(0, new_collection)
        await self._save_collections(current_collections)
        self.is_new_collection_modal_open = False
        self._reset_collection_form()
        return rx.toast.success(f"Collection '{new_collection['name']}' created!")

    @rx.event
    async def handle_edit_submit(self, form_data: dict):
        """Handle form submission to edit an existing collection."""
        if not self.editing_collection:
            return rx.toast.error("No collection selected for editing.")
        name = form_data.get("name", "").strip()
        if not name:
            return rx.toast.error("Collection name cannot be empty.")
        now = datetime.now(timezone.utc).isoformat()
        updated_collections = await self.collections
        for i, c in enumerate(updated_collections):
            if c["id"] == self.editing_collection["id"]:
                updated_collections[i]["name"] = name
                updated_collections[i]["description"] = form_data.get("description", "")
                updated_collections[i]["color"] = self.new_collection_color
                updated_collections[i]["updated_at"] = now
                break
        await self._save_collections(updated_collections)
        self.close_edit_collection_modal()
        return rx.toast.success(f"Collection '{name}' updated!")

    @rx.event
    async def delete_collection(self):
        """Delete the selected collection and all its items."""
        if not self.deleting_collection_id:
            return rx.toast.error("No collection selected for deletion.")
        collections = await self.collections
        updated_collections = [
            c for c in collections if c["id"] != self.deleting_collection_id
        ]
        await self._save_collections(updated_collections)
        items = await self.items
        updated_items = [
            i for i in items if i["collection_id"] != self.deleting_collection_id
        ]
        await self._save_items(updated_items)
        self.close_delete_collection_modal()
        return rx.toast.success("Collection deleted.")

    @rx.event
    def go_to_collection(self, collection_id: str):
        """Navigate to a specific collection's detail page."""
        return rx.redirect(f"/collections/{collection_id}")

    current_collection: Optional[Collection] = None

    @rx.var
    def get_collection_id_from_route(self) -> str:
        """Get the collection ID from the URL."""
        return self.router.page.params.get("collection_id", "")

    @rx.event
    async def on_detail_load(self):
        """Load the collection data when the detail page loads."""
        from app.states.auth_state import AuthState

        auth_state = await self.get_state(AuthState)
        if not auth_state.is_authenticated:
            return rx.redirect("/login")
        self.item_search_query = ""
        collection_id = self.get_collection_id_from_route
        collections = await self.collections
        collection = next((c for c in collections if c["id"] == collection_id), None)
        if collection:
            self.current_collection = collection
        else:
            return rx.redirect("/")

    @rx.event
    def set_item_search_query(self, query: str):
        """Set the item search query for the current collection."""
        self.item_search_query = query

    @rx.event
    def toggle_new_item_modal(self):
        """Toggle the new item modal."""
        self.is_new_item_modal_open = not self.is_new_item_modal_open
        if not self.is_new_item_modal_open:
            self._reset_item_form()
        else:
            self.editing_item = None

    @rx.event
    def open_edit_item_modal(self, item: Item):
        """Open the edit item modal."""
        self.editing_item = item
        self.is_edit_item_modal_open = True

    @rx.event
    def close_edit_item_modal(self):
        """Close the edit item modal."""
        self.is_edit_item_modal_open = False
        self._reset_item_form()

    @rx.event
    def open_delete_item_modal(self, item: Item):
        """Open the delete item modal."""
        self.deleting_item_id = item["id"]
        self.is_delete_item_modal_open = True

    @rx.event
    def close_delete_item_modal(self):
        """Close the delete item modal."""
        self.is_delete_item_modal_open = False
        self.deleting_item_id = None

    async def _update_collection_meta(self, collection_id: str, item_delta: int):
        """Update item count and last updated time for a collection."""
        collections = await self.collections
        now = datetime.now(timezone.utc).isoformat()
        for i, c in enumerate(collections):
            if c["id"] == collection_id:
                collections[i]["item_count"] += item_delta
                collections[i]["updated_at"] = now
                if (
                    self.current_collection
                    and self.current_collection["id"] == collection_id
                ):
                    self.current_collection = collections[i]
                break
        await self._save_collections(collections)

    @rx.event
    async def handle_create_item_submit(self, form_data: dict):
        """Handle creating a new item."""
        if not self.current_collection:
            return rx.toast.error("Cannot add item: no collection context.")
        name = form_data.get("name", "").strip()
        if not name:
            return rx.toast.error("Item name cannot be empty.")
        now = datetime.now(timezone.utc).isoformat()
        tags_str = form_data.get("tags", "")
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        new_item: Item = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": form_data.get("description", ""),
            "tags": tags,
            "collection_id": self.current_collection["id"],
            "created_at": now,
            "updated_at": now,
        }
        current_items = await self.items
        current_items.insert(0, new_item)
        await self._save_items(current_items)
        await self._update_collection_meta(new_item["collection_id"], 1)
        self.is_new_item_modal_open = False
        return rx.toast.success(f"Item '{name}' added.")

    @rx.event
    async def handle_edit_item_submit(self, form_data: dict):
        """Handle editing an existing item."""
        if not self.editing_item:
            return rx.toast.error("No item selected for editing.")
        name = form_data.get("name", "").strip()
        if not name:
            return rx.toast.error("Item name cannot be empty.")
        now = datetime.now(timezone.utc).isoformat()
        tags_str = form_data.get("tags", "")
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        updated_items = await self.items
        for i, item in enumerate(updated_items):
            if item["id"] == self.editing_item["id"]:
                updated_items[i]["name"] = name
                updated_items[i]["description"] = form_data.get("description", "")
                updated_items[i]["tags"] = tags
                updated_items[i]["updated_at"] = now
                break
        await self._save_items(updated_items)
        await self._update_collection_meta(self.editing_item["collection_id"], 0)
        self.close_edit_item_modal()
        return rx.toast.success(f"Item '{name}' updated.")

    @rx.event
    async def delete_item(self):
        """Delete an item."""
        if not self.deleting_item_id:
            return rx.toast.error("No item to delete.")
        items = await self.items
        item_to_delete = next(
            (i for i in items if i["id"] == self.deleting_item_id), None
        )
        if not item_to_delete:
            self.close_delete_item_modal()
            return rx.toast.error("Item not found.")
        updated_items = [i for i in items if i["id"] != self.deleting_item_id]
        await self._save_items(updated_items)
        await self._update_collection_meta(item_to_delete["collection_id"], -1)
        self.close_delete_item_modal()
        return rx.toast.success("Item deleted.")

    @rx.event
    def handle_key_down(self, event):
        """Handle global key presses for shortcuts."""
        if isinstance(event, dict):
            key = event.get("key", "").lower()
            meta_key = event.get("metaKey", False)
            ctrl_key = event.get("ctrlKey", False)
        else:
            key = str(event).lower()
            meta_key = False
            ctrl_key = False
        if (meta_key or ctrl_key) and key == "k":
            if self.router.page.path.startswith("/collections/"):
                return rx.call_script(
                    "document.getElementById('item_search_input').focus(); event.preventDefault();"
                )
            else:
                return rx.call_script(
                    "document.getElementById('collection_search_input').focus(); event.preventDefault();"
                )
        if not (meta_key or ctrl_key) and key == "n":
            if not self.router.page.path.startswith("/collections/"):
                self.is_new_collection_modal_open = True
                return rx.call_script("event.preventDefault();")
        if key == "escape":
            if self.is_new_collection_modal_open:
                yield CollectionsState.toggle_new_collection_modal
            if self.is_edit_collection_modal_open:
                yield CollectionsState.close_edit_collection_modal
            if self.is_delete_collection_modal_open:
                yield CollectionsState.close_delete_collection_modal
            if self.is_new_item_modal_open:
                yield CollectionsState.toggle_new_item_modal
            if self.is_edit_item_modal_open:
                yield CollectionsState.close_edit_item_modal
            if self.is_delete_item_modal_open:
                yield CollectionsState.close_delete_item_modal