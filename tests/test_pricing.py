from decimal import Decimal

from src.pricing import calculate_price, pricing_rule_for_listing


def test_calculate_price_applies_multiplier():
    assert calculate_price("10.00", 0.95, 0.99) == Decimal("9.50")


def test_calculate_price_rounds_to_cents():
    assert calculate_price("10.01", 0.95, 0.99) == Decimal("9.51")


def test_calculate_price_respects_minimum():
    assert calculate_price("0.50", 0.95, 0.99) == Decimal("0.99")


def test_condition_multiplier():
    config = {
        "pricing": {
            "normal_multiplier": 0.95,
            "foil_multiplier": 0.95,
            "minimum_price": 0.99,
            "condition_multipliers": {"NM": 1.0, "LP": 0.9},
        }
    }
    listing = {"finish": "NORMAL", "condition": "LP"}
    assert pricing_rule_for_listing(listing, config) == (0.95, 0.9)
