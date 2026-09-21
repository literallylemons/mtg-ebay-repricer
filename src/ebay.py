import base64
import os
import requests

PRODUCTION_API = "https://api.ebay.com"
SANDBOX_API = "https://api.sandbox.ebay.com"
OAUTH_PRODUCTION = "https://api.ebay.com/identity/v1/oauth2/token"
OAUTH_SANDBOX = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

class EbayError(RuntimeError):
    pass

class EbayClient:
    def __init__(self, environment="production"):
        self.environment = environment.lower()
        if self.environment not in {"production", "sandbox"}:
            raise ValueError("EBAY_ENVIRONMENT must be production or sandbox.")
        self.api_base = PRODUCTION_API if self.environment == "production" else SANDBOX_API
        self.oauth_url = OAUTH_PRODUCTION if self.environment == "production" else OAUTH_SANDBOX
        self.client_id = os.environ.get("EBAY_CLIENT_ID")
        self.client_secret = os.environ.get("EBAY_CLIENT_SECRET")
        self.refresh_token = os.environ.get("EBAY_REFRESH_TOKEN")
        missing = [name for name, value in {
            "EBAY_CLIENT_ID": self.client_id,
            "EBAY_CLIENT_SECRET": self.client_secret,
            "EBAY_REFRESH_TOKEN": self.refresh_token,
        }.items() if not value]
        if missing:
            raise EbayError("Missing eBay credentials: " + ", ".join(missing))

    def access_token(self):
        credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        response = requests.post(
            self.oauth_url,
            headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "refresh_token", "refresh_token": self.refresh_token},
            timeout=30,
        )
        if not response.ok:
            raise EbayError(f"eBay OAuth failed: HTTP {response.status_code}: {response.text}")
        return response.json()["access_token"]

    def _request(self, method, path, **kwargs):
        token = self.access_token()
        headers = kwargs.pop("headers", {})
        headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        response = requests.request(method, f"{self.api_base}{path}", headers=headers, timeout=30, **kwargs)
        if not response.ok:
            raise EbayError(f"eBay API request failed: HTTP {response.status_code}: {response.text}")
        return response.json() if response.content else {}

    def get_inventory_items(self):
        items, offset, limit = [], 0, 100
        while True:
            data = self._request("GET", "/sell/inventory/v1/inventory_item", params={"limit": limit, "offset": offset})
            page = data.get("inventoryItems", [])
            items.extend(page)
            total = data.get("total", len(items))
            if not page or len(items) >= total:
                return items
            offset += len(page)

    def get_offers(self, sku):
        return self._request("GET", "/sell/inventory/v1/offer", params={"sku": sku}).get("offers", [])

    def get_active_offers(self):
        active = []
        for item in self.get_inventory_items():
            sku = item.get("sku")
            if not sku:
                continue
            for offer in self.get_offers(sku):
                if offer.get("status") == "PUBLISHED" and offer.get("listing", {}).get("listingStatus") == "ACTIVE":
                    active.append(offer)
        return active

    def update_price(self, offer_id, price, currency="USD"):
        return self._request(
            "PUT",
            f"/sell/inventory/v1/offer/{offer_id}",
            json={"pricingSummary": {"price": {"currency": currency, "value": str(price)}}},
        )
