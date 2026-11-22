"""S35 acceptance: a stamp's colours are changed from the preview pane.

The writer already accepted `colors` on an update (S12) and S21's revert already
put them back. What these tests pin is the page's half: the rows carry ids
instead of names, the palette travels with the series so a chip has a name and a
tone, and the pane — never the cell — is where the colours are edited.
"""

import json

import pytest
from django.test import Client

from colors_api.models import Color
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year

PAGE_URL = "/datadesk/issues/{pk}/"
NEW_URL = "/datadesk/issues/new/"


@pytest.fixture
def issue(db) -> Issue:
    """One series whose stamp has two colours, written in reverse order."""
    created = Issue.objects.create(
        year=Year.objects.create(year=1853), name="Isabel II"
    )
    red = Color.objects.create(name="Rosa")
    blue = Color.objects.create(name="Azul")
    stamp = Stamp.objects.create(issue=created, name="Isabel II", face_value="6 cs")
    stamp.colors.set([red, blue])
    Stamp.objects.create(issue=created, name="Sin color", face_value="12 cs")
    return created


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """A logged-in staff client."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


def config_of(response) -> dict:
    """Returns the grid configuration the page ships."""
    content = response.content.decode()
    blob = content.split('id="stamp-config" type="application/json">')[1]
    return json.loads(blob.split("</script>")[0])


@pytest.mark.django_db
class TestTheRowsCarryIds:
    """The change set speaks ids, so the rows do too."""

    def test_a_row_sends_the_ids_of_its_colours(self, staff_client, issue) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))
        stamp = issue.stamps.order_by("pk").first()

        assert sorted(config["data"][0]["colors"]) == sorted(
            stamp.colors.values_list("pk", flat=True)
        )
        assert all(isinstance(value, int) for value in config["data"][0]["colors"])

    def test_the_ids_come_ordered_by_name(self, staff_client, issue) -> None:
        """The palette and the row agree, so a chip never jumps about."""
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))
        stamp = issue.stamps.order_by("pk").first()
        expected = [
            colour.pk for colour in sorted(stamp.colors.all(), key=lambda c: c.name)
        ]

        assert config["data"][0]["colors"] == expected

    def test_a_stamp_without_colours_sends_an_empty_list(
        self, staff_client, issue
    ) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        assert config["data"][1]["colors"] == []

    def test_the_workbench_does_not_ship_the_palette(self, mounted, staff_client) -> None:
        """Only the series screen edits colours; the list has no stamp rows."""
        content = staff_client.get("/datadesk/issues/").content.decode()

        assert 'id="stamp-config"' not in content


@pytest.mark.django_db
class TestThePalette:
    """A chip needs the name and the tone of an id it only knows as a number."""

    def test_every_colour_travels_with_its_name_and_tone(
        self, staff_client, issue
    ) -> None:
        palette = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["colours"]

        by_name = {entry["label"]: entry for entry in palette}
        assert set(by_name) == set(Color.objects.values_list("name", flat=True))
        assert by_name["Azul"]["value"] == Color.objects.get(name="Azul").pk
        assert by_name["Azul"]["tone"]


@pytest.mark.django_db
class TestThePaneOwnsTheWidget:
    """The colours are edited in the pane, and nowhere else."""

    def test_the_pane_renders_the_colour_controls(self, staff_client, issue) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        for element in (
            "preview-colours",
            "preview-colours-empty",
            "colour-picker",
            "colour-picker-create",
            "lookup-color",
        ):
            assert f'id="{element}"' in content, element

    def test_the_colour_field_is_not_a_strip_lookup(self, staff_client, issue) -> None:
        """`unresolvedLookup()` blocks the commit on a typed name, which a colour
        picker must not do: a name without a row is created, not refused."""
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        assert 'data-lookup="color"' not in content

    def test_the_new_series_page_has_the_same_control(self, staff_client) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert 'id="colour-picker"' in content
        assert 'id="lookup-color"' in content
