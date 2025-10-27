import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import PermissionDenied
from rest_framework_api_key.models import APIKey

# --- Mocking the External Dependencies ---

# Assuming this is your custom permission class path
from common.core.permissions import HasSpecificKeyName
from common.api.messages import Messages

# Assuming you have a simplified version of your Messages class for testing
class MockMessages:
    class APIKey:
        @staticmethod
        def invalid_key():
            return Messages.Auth.invalid_api_key()

        @staticmethod
        def invalid_user():
            return Messages.Auth.not_enough_rights()

# Replace the actual Messages class with the mock for testing
HasSpecificKeyName.Messages = MockMessages 


@pytest.mark.django_db
class TestHasSpecificKeyName:
    """Tests for the custom HasSpecificKeyName permission class."""

    # 1. Fixture to create a valid API key for all tests in this class
    @pytest.fixture(autouse=True)
    def setup_key(self, db):
        # Create a key object and get the raw key (prefix + secret)
        self.api_key_obj, self.raw_key = APIKey.objects.create_key(name="ValidKeyName")
        self.factory = APIRequestFactory()
        # The key name that must match the header
        self.key_name = self.api_key_obj.name

    # 3. Test for the authentication failure: Key is invalid (testing the super() call)
    def test_permission_denied_on_invalid_key(self, mocker):
        """Should raise PermissionDenied when the parent (HasAPIKey) fails."""

        # --- Arrange (Setup for parent failure) ---
        request = self.factory.get('/')
        # Don't provide the API Key header, or provide a known-invalid one
        request.META['HTTP_AUTHORIZATION'] = 'API-Key abcdesdsdsdssdsds' 
        mock_view = None
        
        # Mock the super's has_permission method to simulate its failure
        # In this scenario, `super().has_permission` would typically raise NotAuthenticated 
        # or similar, but since your code *explicitly* checks the return value and raises
        # PermissionDenied, we simulate the return value:
        mocker.patch(
            'rest_framework_api_key.permissions.HasAPIKey.has_permission', 
            return_value=False
        )

        # --- Act & Assert ---
        permission = HasSpecificKeyName()
        
        # The permission check should raise a PermissionDenied exception
        with pytest.raises(PermissionDenied) as excinfo:
            permission.has_permission(request, mock_view)

        # Check the specific error message from your parent failure block
        assert MockMessages.APIKey.invalid_key() in str(excinfo.value.detail)