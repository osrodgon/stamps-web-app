"""Tests for the source registry and the adapter contract (plan step A2)."""

import pytest

from ai_api.sources import registry
from ai_api.sources.base import SourceAdapter


class DummyAdapter(SourceAdapter):
    """Stand-in for the adapters A3 and A6 will register."""

    name = "dummy"

    def supports(self, subject) -> bool:
        return True

    def fetch(self, subject) -> list:
        return []


class UnnamedAdapter(SourceAdapter):
    """An adapter that forgot its name, which the registry must refuse."""

    def supports(self, subject) -> bool:
        return True

    def fetch(self, subject) -> list:
        return []


@pytest.fixture(autouse=True)
def clean_registry():
    """Keep the module-level registry from leaking between tests."""
    registry.clear()
    yield
    registry.clear()


class TestRegistry:
    """Name in, adapter out."""

    def test_register_and_get(self):
        registry.register(DummyAdapter)

        assert registry.get("dummy") is DummyAdapter
        assert registry.available() == ["dummy"]

    def test_an_unknown_name_says_what_is_registered(self):
        registry.register(DummyAdapter)

        with pytest.raises(KeyError) as error:
            registry.get("colnect")

        assert "dummy" in str(error.value)

    def test_an_adapter_without_a_name_is_refused(self):
        with pytest.raises(ValueError):
            registry.register(UnnamedAdapter)

    def test_the_list_is_sorted(self):
        registry.register(DummyAdapter)
        assert registry.available() == ["dummy"]

    def test_unregister_forgets_only_one(self):
        registry.register(DummyAdapter)

        registry.unregister("dummy")

        assert registry.available() == []


class TestContract:
    """The adapter has to answer both questions."""

    def test_an_adapter_cannot_be_instantiated_without_its_methods(self):
        class Incomplete(SourceAdapter):
            name = "incomplete"

        with pytest.raises(TypeError):
            Incomplete()

    def test_the_dummy_implements_the_contract(self):
        adapter = DummyAdapter()

        assert adapter.supports(object()) is True
        assert adapter.fetch(object()) == []
