import requests
from urllib.parse import quote

SCRYFALL_API = "https://api.scryfall.com/cards"
HEADERS = {
    "User-Agent": "mtg-ebay-repricer/1.0",
    "Accept": "application/json",
}


def _get(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_card(scryfall_id):
    return _get(f"{SCRYFALL_API}/{quote(str(scryfall_id), safe='')}")


def get_card_by_printing(set_code, collector_number):
    return _get(
        f"{SCRYFALL_API}/{quote(str(set_code).lower(), safe='')}/"
        f"{quote(str(collector_number), safe='')}"
    )


def get_usd_price(card, finish):
    prices = card.get("prices", {})
    value = prices.get("usd_foil") if finish == "FOIL" else prices.get("usd")
    if value is None:
        raise ValueError(
            f"No USD price available for Scryfall card {card.get('id')} "
            f"with finish {finish}."
        )
    return float(value)
