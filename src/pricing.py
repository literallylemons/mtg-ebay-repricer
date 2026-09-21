from decimal import Decimal, ROUND_HALF_UP


def calculate_price(market_price, multiplier, minimum_price):
    price = Decimal(str(market_price)) * Decimal(str(multiplier))
    price = price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    minimum = Decimal(str(minimum_price))
    return max(price, minimum)
