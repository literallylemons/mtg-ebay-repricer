import pytest

from src.listings import parse_sku, validate_listings


@pytest.mark.parametrize(
    "sku",
    [
        "PIP-11-NORMAL-NM",
        "MH3-154-FOIL-LP",
        "DMU-123-NORMAL-HP",
        "SLD-796-FOIL-D",
    ],
)
def test_valid_skus(sku):
    parsed = parse_sku(sku)
    assert parsed["finish"] in {"FOIL", "NORMAL"}
    assert parsed["condition"] in {"NM", "LP", "HP", "D"}


@pytest.mark.parametrize(
    "sku",
    [
        "pip-11-NORMAL-NM",
        "PIP-011-NORMAL-NM",
        "PIP-11-REGULAR-NM",
        "PIP-11-NORMAL-MP",
        "PIP-11-NORMAL",
        "PIP-0-NORMAL-NM",
    ],
)
def test_invalid_skus(sku):
    with pytest.raises(ValueError):
        parse_sku(sku)


def test_duplicate_skus_are_reported():
    listings = [
        {
            "sku": "PIP-11-NORMAL-NM",
            "set": "PIP",
            "collector_number": "11",
            "finish": "NORMAL",
            "condition": "NM",
        },
        {
            "sku": "PIP-11-NORMAL-NM",
            "set": "PIP",
            "collector_number": "11",
            "finish": "NORMAL",
            "condition": "NM",
        },
    ]

    errors = validate_listings(listings)

    assert any("Duplicate SKU" in error for error in errors)


def test_sku_data_mismatch_is_reported():
    listing = {
        "sku": "PIP-11-FOIL-NM",
        "set": "PIP",
        "collector_number": "11",
        "finish": "NORMAL",
        "condition": "NM",
    }

    errors = validate_listings([listing])

    assert any("SKU mismatch" in error for error in errors)
