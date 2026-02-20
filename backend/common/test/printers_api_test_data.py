import pytest
from printers_api.models import Printer

@pytest.fixture
def printers_table():
    """
    Fixture to create a list of Printer objects for testing.
    """
    printers = [
        Printer.objects.create(name="Printer One"),
        Printer.objects.create(name="Printer Two"),
        Printer.objects.create(name="Printer Three"),
    ]
    return printers

@pytest.fixture
def printer_post_payload_ok():
    """
    Fixture for a valid printer creation payload.
    """
    return {"name": "Printer Four"}

@pytest.fixture
def printer_put_payload_ok():
    """
    Fixture for a valid printer update payload.
    """
    return {"name": "Printer Five"}
