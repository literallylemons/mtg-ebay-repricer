import requests

SCRYFALL_API = "https://api.scryfall.com/cards"


def get_card(scryfall_id):
    response = requests.get(
        f"{SCRYFALL_API}/{scryfall_id}",
        headers={"User-Agent": "mtg-ebay-repricer/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_usd_price(card, finish):
    prices = card.get("prices", {})

    if finish == "FOIL":
        value = prices.get("usd_foil")
    else:
        value = prices.get("usd")

    if value is None:
        raise ValueError(
            f"No USD price available for Scryfall card {card.get('id')} "
            f"with finish {finish}."
        )

    return float(value)
