import logging
import pytest
from core.translations import _
from core.urls import URLs
from nicegui.testing import User
from pages.collection.collections_page import CollectionsPage
from components.common.top_bar import TopBar
from tests.helpers.abstract_unit_test import AbstractUnitTest


@pytest.mark.asyncio
class TestCollectionsPage(AbstractUnitTest):
    """
    Unit tests for the CollectionsPage component.
    
    This class verifies the functionality of the collections page,
    including UI setup and component initialization.
    """
    
    @pytest.fixture(autouse=True)
    def init_data(self, mocker, caplog):
        """Initializes mock data and configures logging for tests."""
        caplog.set_level(logging.CRITICAL)
        self._AbstractUnitTest__mocker = mocker
        
    @pytest.fixture
    async def collections_page_components(self, user: User):
        """
        Fixture that opens the collections page and retrieves key components.
        
        Args:
            user (User): The NiceGUI testing user instance.
            
        Returns:
            tuple: A tuple containing (collections_page, top_bar).
        """
        collections_object = await user.open(URLs.Frontend.collections)
        collections_page = self.get_component(collections_object, CollectionsPage)
        top_bar = self.get_component(collections_object, TopBar)
        
        assert collections_page is not None
        assert top_bar is not None
        yield collections_page, top_bar
        
    async def test_page_initialization(self, collections_page_components):
        """
        Verifies that the CollectionsPage initializes correctly.
        """
        collections_page, top_bar = collections_page_components
        
        # Verify components are initialized
        assert isinstance(collections_page, CollectionsPage)
        assert isinstance(top_bar, TopBar)
        
        # Verify page title
        assert top_bar.title == _('collections_tile')  # This will be translated by the actual app
        
    async def test_page_inheritance(self, collections_page_components):
        """
        Verifies that the CollectionsPage properly inherits from BasePage and ui.column.
        """
        collections_page, top_bar = collections_page_components
        
        # Verify inheritance
        from base.base_page import BasePage
        from nicegui import ui
        
        assert isinstance(collections_page, BasePage)
        assert isinstance(collections_page, ui.column)
        
    async def test_page_structure(self, collections_page_components):
        """
        Verifies that the CollectionsPage has the expected structure.
        """
        collections_page, top_bar = collections_page_components
        
        # Verify that top_bar is set
        assert collections_page.top_bar is not None
        assert isinstance(collections_page.top_bar, TopBar)