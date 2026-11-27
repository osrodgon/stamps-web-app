"""Unit tests for the collection dialogs (plan step A5).

Both dialogs are built without a page: `ft.Page` is mocked, as the stamp form tests
do. What is checked is the contract — when the service is called, what it receives,
when the dialog closes and when it does not.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
import flet as ft
import requests

from components.form.dialogs.collection_form import (
    CollectionDeleteDialog,
    CollectionForm,
)

COLLECTION = {
    "id": 7,
    "name": "Isabel II",
    "series": 3,
    "stamps": 9,
    "total": 14,
    "covers": [],
}


class Responses:
    """Server answers, without a server."""

    @staticmethod
    def status(code: int) -> MagicMock:
        """A response with that status code."""
        response = MagicMock(spec=requests.Response)
        response.status_code = code
        return response


class DialogTest:
    """The page and the service both dialogs need."""

    @pytest.fixture
    def page(self) -> MagicMock:
        page = MagicMock(spec=ft.Page)
        page.overlay = []
        page.update = MagicMock()
        return page

    @pytest.fixture
    def service(self) -> MagicMock:
        service = MagicMock()
        service.create_collection = AsyncMock()
        service.update_collection = AsyncMock()
        service.delete_collection = AsyncMock()
        return service


class TestCreate(DialogTest):
    """Creating asks for a name and calls the service once."""

    def test_it_opens_a_dialog(self, page, service):
        form = CollectionForm(page, service)

        form.show()

        assert form._dialog.open is True
        assert len(page.overlay) == 1

    def test_the_name_field_does_not_stretch_the_dialog(self, page, service):
        """A text field expands by default; in a dialog that is full height."""
        form = CollectionForm(page, service)

        assert form._name.expand is False
        assert form._name.width == CollectionForm.WIDTH

    async def test_an_empty_name_is_refused(self, page, service):
        form = CollectionForm(page, service)
        form.show()
        form._name.value = "   "

        await form._submit(None)

        service.create_collection.assert_not_awaited()
        assert form._error.visible is True
        assert form._dialog.open is True

    async def test_a_name_creates_the_collection(self, page, service):
        saved = MagicMock()
        service.create_collection.return_value = Responses.status(201)
        form = CollectionForm(page, service, on_saved=saved)
        form.show()
        form._name.value = "  My collection  "

        await form._submit(None)

        service.create_collection.assert_awaited_once_with("My collection")
        assert form._dialog.open is False
        saved.assert_called_once_with()

    async def test_a_forbidden_closes_and_reports(self, page, service):
        forbidden = MagicMock()
        service.create_collection.return_value = Responses.status(403)
        form = CollectionForm(page, service, on_forbidden=forbidden)
        form.show()
        form._name.value = "Mine"

        await form._submit(None)

        assert form._dialog.open is False
        forbidden.assert_called_once_with()

    async def test_a_failure_keeps_the_dialog_open(self, page, service):
        service.create_collection.return_value = Responses.status(500)
        form = CollectionForm(page, service)
        form.show()
        form._name.value = "Mine"

        await form._submit(None)

        assert form._dialog.open is True
        assert form._error.visible is True


class TestRename(DialogTest):
    """Renaming is the same dialog with the old name in it."""

    def test_it_prefills_the_name(self, page, service):
        form = CollectionForm(page, service, collection=COLLECTION)

        form.show()

        assert form._name.value == "Isabel II"

    async def test_it_calls_update_with_the_id(self, page, service):
        service.update_collection.return_value = Responses.status(200)
        form = CollectionForm(page, service, collection=COLLECTION)
        form.show()
        form._name.value = "Isabel II (1850)"

        await form._submit(None)

        service.update_collection.assert_awaited_once_with(7, "Isabel II (1850)")
        assert form._dialog.open is False


class TestDelete(DialogTest):
    """Deleting asks once and calls the service only on confirm."""

    async def test_confirming_deletes(self, page, service):
        deleted = MagicMock()
        service.delete_collection.return_value = Responses.status(200)
        dialog = CollectionDeleteDialog(
            page, service, COLLECTION, on_deleted=deleted
        )
        dialog.show()

        await dialog._confirm(None)

        service.delete_collection.assert_awaited_once_with(7)
        assert dialog._dialog.open is False
        deleted.assert_called_once_with()

    async def test_it_says_what_goes_with_the_collection(self, page, service, mocker):
        mocker.patch(
            "components.form.dialogs.collection_form._",
            side_effect=lambda key, **values: f"{key}:{values.get('name', '')}",
        )
        dialog = CollectionDeleteDialog(page, service, COLLECTION)

        dialog.show()

        texts = [control.value for control in dialog._dialog.content.controls]
        assert any("Isabel II" in str(text) for text in texts)

    async def test_cancelling_does_not_delete(self, page, service):
        dialog = CollectionDeleteDialog(page, service, COLLECTION)
        dialog.show()

        dialog._close(None)

        service.delete_collection.assert_not_awaited()
        assert dialog._dialog.open is False

    async def test_a_forbidden_closes_and_reports(self, page, service):
        forbidden = MagicMock()
        service.delete_collection.return_value = Responses.status(403)
        dialog = CollectionDeleteDialog(
            page, service, COLLECTION, on_forbidden=forbidden
        )
        dialog.show()

        await dialog._confirm(None)

        assert dialog._dialog.open is False
        forbidden.assert_called_once_with()

    async def test_a_failure_keeps_the_dialog_open(self, page, service):
        service.delete_collection.return_value = Responses.status(500)
        dialog = CollectionDeleteDialog(page, service, COLLECTION)
        dialog.show()

        await dialog._confirm(None)

        assert dialog._dialog.open is True
        assert dialog._error.visible is True
