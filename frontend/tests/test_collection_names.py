"""The collection names the screens keep, so they are not fetched again (2026-11-28)."""

from core.collection_names import CollectionNames


class TestRemember:
    """Remembering, reading and dropping one name."""

    def test_a_remembered_name_is_read_back(self):
        CollectionNames.remember(7, "Test")

        assert CollectionNames.get(7) == "Test"

    def test_an_unknown_collection_has_no_name(self):
        assert CollectionNames.get(7) is None

    def test_an_empty_name_is_not_kept(self):
        CollectionNames.remember(7, "")

        assert CollectionNames.get(7) is None

    def test_remembering_again_overrides_it(self):
        CollectionNames.remember(7, "Test")
        CollectionNames.remember(7, "Test 2")

        assert CollectionNames.get(7) == "Test 2"

    def test_forgetting_one_leaves_the_others(self):
        CollectionNames.remember(7, "Test")
        CollectionNames.remember(8, "Other")

        CollectionNames.forget(7)

        assert CollectionNames.get(7) is None
        assert CollectionNames.get(8) == "Other"

    def test_forgetting_something_unknown_is_quiet(self):
        CollectionNames.forget(99)

        assert CollectionNames.get(99) is None
