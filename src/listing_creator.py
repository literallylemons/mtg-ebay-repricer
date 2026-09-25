import html
import re

from src.scryfall import get_card_by_printing, get_usd_price

CATEGORY_ID = "183454"

CONDITION_DESCRIPTOR_VALUES = {
    "NM": "400010",
    "LP": "400015",
    "HP": "400017",
    "D": "400013",
}

LANGUAGE_NAMES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ja": "Japanese", "ko": "Korean",
    "ru": "Russian", "zhs": "Chinese Simplified", "zht": "Chinese Traditional",
    "ph": "Phyrexian", "he": "Hebrew", "grc": "Ancient Greek", "la": "Latin",
    "ar": "Arabic",
}

FINISH_NAMES = {"NORMAL": "Non-Foil", "FOIL": "Foil"}

def normalize_card_number(number):
    value = str(number).strip().upper()
    if not value or not re.fullmatch(r"[1-9][A-Z0-9★._/]*", value):
        raise ValueError("Card number must be a valid Scryfall collector number.")
    return value

def build_sku(set_code, collector_number, finish, condition):
    set_code = str(set_code).strip().upper()
    collector_number = normalize_card_number(collector_number)
    finish = str(finish).strip().upper()
    condition = str(condition).strip().upper()
    if not re.fullmatch(r"[A-Z0-9]+", set_code):
        raise ValueError("Set code must contain only letters and numbers.")
    if finish not in FINISH_NAMES:
        raise ValueError("Finish must be NORMAL or FOIL.")
    if condition not in CONDITION_DESCRIPTOR_VALUES:
        raise ValueError("Condition must be NM, LP, HP, or D.")
    return f"{set_code}-{collector_number}-{finish}-{condition}"

def prepare_listing_data(set_code, collector_number, finish, condition, language, quantity):
    set_code = str(set_code).strip().upper()
    collector_number = normalize_card_number(collector_number)
    finish = str(finish).strip().upper()
    condition = str(condition).strip().upper()
    language = str(language).strip().lower()
    quantity = int(quantity)

    if finish not in FINISH_NAMES:
        raise ValueError("Finish must be NORMAL or FOIL.")
    if condition not in CONDITION_DESCRIPTOR_VALUES:
        raise ValueError("Condition must be NM, LP, HP, or D.")
    if language not in LANGUAGE_NAMES:
        raise ValueError("Unsupported language code. Use a Scryfall language code such as en or ja.")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    card = get_card_by_printing(set_code, collector_number)
    if card.get("lang") != language:
        raise ValueError(
            f"Scryfall returned language '{card.get('lang')}' for {set_code} {collector_number}, "
            f"but '{language}' was requested."
        )

    image_url = card.get("image_uris", {}).get("large") or card.get("image_uris", {}).get("normal")
    if not image_url:
        raise ValueError("Scryfall did not provide an image URL for this card.")

    market_price = get_usd_price(card, finish)
    price = max(round(market_price * 0.95 + 1e-9, 2), 0.99)
    sku = build_sku(set_code, collector_number, finish, condition)

    card_name = card.get("name", "Unknown Card")
    set_name = card.get("set_name", set_code)
    type_line = card.get("type_line", "")
    rarity = card.get("rarity", "").replace("_", " ").title()
    language_name = LANGUAGE_NAMES[language]
    finish_name = FINISH_NAMES[finish]

    title = f"{card_name} | {set_name} #{collector_number} | {finish_name}"[:80]
    description = f"""<div>
<h2>{html.escape(card_name)}</h2>
<p><strong>Set:</strong> {html.escape(set_name)}<br>
<strong>Card Number:</strong> {html.escape(collector_number)}<br>
<strong>Card Type:</strong> {html.escape(type_line)}<br>
<strong>Rarity:</strong> {html.escape(rarity)}<br>
<strong>Language:</strong> {html.escape(language_name)}<br>
<strong>Finish:</strong> {html.escape(finish_name)}<br>
<strong>Condition:</strong> {html.escape(condition)}</p>
<p>Authentic Magic: The Gathering card.</p>
</div>"""

    item_specifics = {
        "Game": "Magic: The Gathering",
        "Card Name": card_name,
        "Set": set_name,
        "Card Number": collector_number,
        "Card Type": type_line,
        "Rarity": rarity,
        "Language": language_name,
        "Finish": finish_name,
        "Manufacturer": "Wizards of the Coast",
    }

    return {
        "sku": sku, "title": title, "description": description,
        "category_id": CATEGORY_ID, "price": price, "market_price": market_price,
        "quantity": quantity, "image_url": image_url, "item_specifics": item_specifics,
        "condition_descriptor_value": CONDITION_DESCRIPTOR_VALUES[condition],
        "card": card,
    }
