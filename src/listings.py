import json
from pathlib import Path
import re

LISTINGS_FILE = Path("data/listings.json")

SKU_PATTERN = re.compile(
    r"^(?P<set>[A-Z0-9]+)-(?P<number>[1-9][A-Z0-9★._/]*)-"
    r"(?P<finish>FOIL|NORMAL)-(?P<condition>NM|LP|HP|D)$"
)


def load_listings():
    with LISTINGS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_listings(listings):
    LISTINGS_FILE.write_text(
        json.dumps(listings, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_sku(sku):
    if not isinstance(sku, str):
        raise ValueError("SKU must be a string.")
    match = SKU_PATTERN.fullmatch(sku)
    if not match:
        raise ValueError(
            f"Invalid SKU '{sku}'. Expected SET-CARDNUMBER-FOILTYPE-CONDITION."
        )
    return match.groupdict()


def validate_listings(listings):
    errors = []
    seen = {}

    for index, listing in enumerate(listings):
        sku = listing.get("sku")
        if not isinstance(sku, str):
            errors.append(f"Listing {index + 1}: missing SKU.")
            continue

        try:
            parsed = parse_sku(sku)
        except ValueError as error:
            errors.append(f"Listing {index + 1}: {error}")
            continue

        if sku in seen:
            errors.append(
                f"Duplicate SKU '{sku}' found in listings "
                f"{seen[sku] + 1} and {index + 1}."
            )
        else:
            seen[sku] = index

        expected = {
            "set": str(listing.get("set", "")).upper(),
            "number": str(listing.get("collector_number", "")).upper(),
            "finish": str(listing.get("finish", "")).upper(),
            "condition": str(listing.get("condition", "")).upper(),
        }

        for field in expected:
            if expected[field] != parsed[field]:
                errors.append(
                    f"SKU mismatch for '{sku}': {field} does not match "
                    f"the listing data."
                )
    return errors


def normalize_ebay_offer(offer):
    sku = offer.get("sku")
    parsed = parse_sku(sku)
    price = offer.get("pricingSummary", {}).get("price", {})
    listing = offer.get("listing", {})

    item_id = str(
        offer.get("itemId")
        or offer.get("itemID")
        or offer.get("ItemID")
        or ""
    )
    offer_id = str(
        offer.get("offerId")
        or offer.get("offerID")
        or ""
    )
    listing_id = str(
        offer.get("listingId")
        or listing.get("listingId")
        or listing.get("itemId")
        or ""
    )

    if not listing_id:
        listing_id = item_id or offer_id

    if not offer_id:
        offer_id = item_id or listing_id

    if not item_id:
        item_id = listing_id or offer_id

    return {
        "sku": sku,
        "set": parsed["set"],
        "collector_number": parsed["number"],
        "finish": parsed["finish"],
        "condition": parsed["condition"],
        "offer_id": offer_id,
        "listing_id": listing_id,
        "listing_status": listing.get("listingStatus"),
        "status": offer.get("status"),
        "marketplace_id": offer.get("marketplaceId"),
        "currency": price.get("currency"),
        "current_price": price.get("value"),
        "quantity": offer.get("availableQuantity"),
    }
