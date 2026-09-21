from decimal import Decimal, ROUND_HALF_UP


def calculate_price(
    market_price,
    multiplier,
    minimum_price,
    condition_multiplier=1.0,
):
    price = (
        Decimal(str(market_price))
        * Decimal(str(multiplier))
        * Decimal(str(condition_multiplier))
    )
    price = price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    minimum = Decimal(str(minimum_price))
    return max(price, minimum)


def pricing_rule_for_listing(listing, config):
    pricing = config["pricing"]
    multiplier = (
        pricing["foil_multiplier"]
        if listing["finish"] == "FOIL"
        else pricing["normal_multiplier"]
    )
    condition_multiplier = pricing.get(
        "condition_multipliers", {}
    ).get(listing["condition"], 1.0)
    return multiplier, condition_multiplier
