import json
from pathlib import Path

from src.listings import normalize_ebay_offer, validate_listings
from src.pricing import calculate_price, pricing_rule_for_listing
from src.scryfall import get_card_by_printing, get_usd_price

CONFIG_FILE = Path("config.json")

def load_config():
    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)

def prepare_listing(offer):
    listing = normalize_ebay_offer(offer)
    listing["scryfall_card"] = get_card_by_printing(listing["set"], listing["collector_number"])
    listing["market_price"] = get_usd_price(listing["scryfall_card"], listing["finish"])
    return listing

def calculate_listing_price(listing, config):
    multiplier, condition_multiplier = pricing_rule_for_listing(listing, config)
    return calculate_price(listing["market_price"], multiplier, config["pricing"]["minimum_price"], condition_multiplier)

def validate_ebay_offers(offers):
    normalized, errors, seen = [], [], {}
    for index, offer in enumerate(offers):
        try:
            listing = normalize_ebay_offer(offer)
        except (ValueError, TypeError) as error:
            errors.append({"sku": offer.get("sku", "<missing>"), "reason": str(error)})
            continue
        sku = listing["sku"]
        if sku in seen:
            errors.append({"sku": sku, "reason": f"Duplicate SKU also found at offer index {seen[sku] + 1}."})
            continue
        seen[sku] = index
        normalized.append(listing)
    errors.extend({"sku": "<validation>", "reason": error} for error in validate_listings(normalized))
    return normalized, errors

def build_repricing_plan(offers, config):
    report = {"updates": [], "no_changes": [], "skips": [], "errors": []}
    valid, validation_errors = validate_ebay_offers(offers)
    report["errors"].extend(validation_errors)
    for offer in valid:
        try:
            listing = prepare_listing(offer)
            if not listing["offer_id"]:
                report["skips"].append({"sku": listing["sku"], "reason": "Missing eBay offer ID."})
                continue
            if listing["current_price"] is None:
                report["skips"].append({"sku": listing["sku"], "reason": "Current eBay price is missing."})
                continue
            new_price = calculate_listing_price(listing, config)
            current_price = calculate_price(listing["current_price"], 1, 0)
            if current_price == new_price:
                report["no_changes"].append({"sku": listing["sku"], "price": str(current_price)})
                continue
            report["updates"].append({
                "sku": listing["sku"], "offer_id": listing["offer_id"], "listing_id": listing["listing_id"],
                "currency": listing["currency"] or config["runtime"]["currency"],
                "old_price": str(current_price), "new_price": str(new_price),
                "market_price": listing["market_price"],
            })
        except Exception as error:
            report["errors"].append({"sku": offer.get("sku", "<missing>"), "reason": str(error)})
    return report
