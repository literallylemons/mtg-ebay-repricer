import json
from pathlib import Path
import re

LISTINGS_FILE = Path("data/listings.json")

SKU_PATTERN = re.compile(
    r"^(?P<set>[A-Z0-9]+)-(?P<number>[1-9][0-9]*)-(?P<finish>FOIL|NORMAL)-(?P<condition>NM|LP|HP|D)$"
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
            errors.append(str(error))
            continue

        if sku in seen:
            errors.append(
                f"Duplicate SKU '{sku}' found in listings "
                f"{seen[sku] + 1} and {index + 1}."
            )
        else:
            seen[sku] = index

        expected = {
            "set": listing.get("set"),
            "number": str(listing.get("collector_number", "")),
            "finish": listing.get("finish"),
            "condition": listing.get("condition"),
        }

        for field in expected:
            if expected[field] != parsed[field]:
                errors.append(
                    f"SKU mismatch for '{sku}': {field} does not match "
                    f"the listing data."
                )

    return errors
