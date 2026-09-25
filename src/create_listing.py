import os

from src.ebay import EbayClient
from src.listing_creator import prepare_listing_data

def main():
    data = prepare_listing_data(
        os.environ["CARD_SET"], os.environ["CARD_NUMBER"], os.environ["CARD_FINISH"],
        os.environ["CARD_CONDITION"], os.environ["CARD_LANGUAGE"], int(os.environ["CARD_QUANTITY"]),
    )
    client = EbayClient(os.environ.get("EBAY_ENVIRONMENT", "sandbox"))

    existing = next((
        offer for offer in client.get_active_offers()
        if offer.get("sku") == data["sku"] and not offer.get("variation")
    ), None)

    if existing:
        current_quantity = int(existing.get("availableQuantity") or 0)
        new_quantity = current_quantity + data["quantity"]
        client.update_quantity(existing["offerId"], new_quantity, sku=data["sku"])
        print("Existing Sandbox listing found.")
        print(f"SKU: {data['sku']}")
        print(f"Existing available quantity: {current_quantity}")
        print(f"Added quantity: {data['quantity']}")
        print(f"New available quantity: {new_quantity}")
        print(f"eBay item ID: {existing['offerId']}")
        return

    result = client.create_fixed_price_listing(
        sku=data["sku"], title=data["title"], description=data["description"],
        category_id=data["category_id"], price=data["price"], quantity=data["quantity"],
        image_url=data["image_url"], item_specifics=data["item_specifics"],
        condition_descriptor_value=data["condition_descriptor_value"],
    )
    print("New Sandbox listing created.")
    print(f"SKU: {data['sku']}")
    print(f"Card: {data['card'].get('name')}")
    print(f"Set: {data['card'].get('set_name')}")
    print(f"Scryfall market price: ${data['market_price']:.2f}")
    print(f"eBay listing price: ${data['price']:.2f}")
    print(f"Quantity: {data['quantity']}")
    print(f"eBay item ID: {result['item_id']}")

if __name__ == "__main__":
    main()