from decimal import Decimal

from src.pricing import calculate_price


def test_calculate_price_applies_multiplier():
    assert calculate_price("10.00", 0.95, 0.99) == Decimal("9.50")


def test_calculate_price_rounds_to_cents():
    assert calculate_price("10.01", 0.95, 0.99) == Decimal("9.51")


def test_calculate_price_respects_minimum():
    assert calculate_price("0.50", 0.95, 0.99) == Decimal("0.99")
