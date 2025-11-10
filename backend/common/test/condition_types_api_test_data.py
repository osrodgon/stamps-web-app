import pytest
from condition_types_api.models import ConditionType

@pytest.fixture
def condition_types_table(db):
    condition_types = [
        ConditionType.objects.create(name="Mint"),
        ConditionType.objects.create(name="Used"),
        ConditionType.objects.create(name="Damaged"),
    ]
    return condition_types

@pytest.fixture
def condition_type_post_payload_ok(db):
    return {
        "name": "New Condition"
    }

@pytest.fixture
def condition_type_put_payload_ok(db):
    return {
        "name": "Updated Condition"
    }