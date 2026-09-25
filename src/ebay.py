import base64
import os
import requests
import xml.etree.ElementTree as ET

PRODUCTION_API = "https://api.ebay.com"
SANDBOX_API = "https://api.sandbox.ebay.com"
OAUTH_PRODUCTION = "https://api.ebay.com/identity/v1/oauth2/token"
OAUTH_SANDBOX = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

TRADING_API_PATH = "/ws/api.dll"
TRADING_API_VERSION = "1477"
EBAY_US_SITE_ID = "0"

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
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        response = requests.post(
            self.oauth_url,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            timeout=30,
        )
        if not response.ok:
            raise EbayError(
                f"eBay OAuth failed: HTTP {response.status_code}: {response.text}"
            )
        return response.json()["access_token"]

    def _request(self, method, path, **kwargs):
        token = self.access_token()
        headers = kwargs.pop("headers", {})
        headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        response = requests.request(
            method,
            f"{self.api_base}{path}",
            headers=headers,
            timeout=30,
            **kwargs,
        )
        if not response.ok:
            raise EbayError(
                f"eBay API request failed: HTTP {response.status_code}: {response.text}"
            )
        return response.json() if response.content else {}

    def _trading_request(self, call_name, body):
        token = self.access_token()
        envelope = ET.Element(
            "Request",
            {
                "xmlns": "urn:ebay:apis:eBLBaseComponents",
            },
        )
        # Replace the placeholder root with the actual Trading API request element.
        root = ET.Element(
            f"{call_name}Request",
            {"xmlns": "urn:ebay:apis:eBLBaseComponents"},
        )
        requester = ET.SubElement(root, "RequesterCredentials")
        ET.SubElement(requester, "eBayAuthToken").text = token
        ET.SubElement(root, "ErrorLanguage").text = "en_US"
        ET.SubElement(root, "Version").text = TRADING_API_VERSION
        for element in body:
            root.append(element)

        xml_body = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        response = requests.post(
            f"{self.api_base}{TRADING_API_PATH}",
            headers={
                "X-EBAY-API-CALL-NAME": call_name,
                "X-EBAY-API-SITEID": EBAY_US_SITE_ID,
                "X-EBAY-API-COMPATIBILITY-LEVEL": TRADING_API_VERSION,
                "Content-Type": "text/xml",
            },
            data=xml_body,
            timeout=60,
        )
        if not response.ok:
            raise EbayError(
                f"eBay Trading API request failed: HTTP {response.status_code}: {response.text}"
            )

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as error:
            raise EbayError(f"Could not parse eBay Trading API response: {error}") from error

        ack = root.find("{urn:ebay:apis:eBLBaseComponents}Ack")
        if ack is not None and ack.text not in {"Success", "Warning"}:
            errors = []
            for error_node in root.findall(
                "{urn:ebay:apis:eBLBaseComponents}Errors"
            ):
                short_message = error_node.find(
                    "{urn:ebay:apis:eBLBaseComponents}ShortMessage"
                )
                long_message = error_node.find(
                    "{urn:ebay:apis:eBLBaseComponents}LongMessage"
                )
                errors.append(
                    (long_message.text if long_message is not None else None)
                    or (short_message.text if short_message is not None else None)
                    or "Unknown eBay Trading API error."
                )
            raise EbayError(
                "eBay Trading API returned "
                + (ack.text or "an error")
                + ": "
                + " | ".join(errors)
            )

        return root

    @staticmethod
    def _text(parent, path, default=None):
        node = parent.find(f"{{urn:ebay:apis:eBLBaseComponents}}{path}")
        return node.text if node is not None else default

    @staticmethod
    def _amount(parent, path):
        node = parent.find(f"{{urn:ebay:apis:eBLBaseComponents}}{path}")
        if node is None:
            return None, None
        return node.text, node.attrib.get("currencyID")

    def get_active_offers(self):
        active = []
        page_number = 1

        while True:
            active_list = ET.Element("ActiveList")
            ET.SubElement(active_list, "Include",).text = "true"
            ET.SubElement(active_list, "IncludeNotes").text = "false"
            pagination = ET.SubElement(active_list, "Pagination")
            ET.SubElement(pagination, "EntriesPerPage").text = "200"
            ET.SubElement(pagination, "PageNumber").text = str(page_number)
            ET.SubElement(active_list, "HideVariations").text = "false"

            root = self._trading_request("GetMyeBaySelling", [active_list])
            ns = "{urn:ebay:apis:eBLBaseComponents}"
            item_array = root.find(
                f"{ns}ActiveList/{ns}ItemArray"
            )

            if item_array is not None:
                for item in item_array.findall(f"{ns}Item"):
                    listing_type = self._text(item, "ListingType")
                    if listing_type != "FixedPriceItem":
                        continue

                    item_id = self._text(item, "ItemID")
                    quantity = int(self._text(item, "Quantity", "0") or 0)
                    quantity_sold = int(
                        self._text(
                            item,
                            "SellingStatus/QuantitySold",
                            "0",
                        )
                        or 0
                    )
                    selling_status = item.find(f"{ns}SellingStatus")
                    price, currency = self._amount(
                        selling_status,
                        "CurrentPrice",
                    ) if selling_status is not None else (None, None)

                    variations = item.find(f"{ns}Variations")
                    if variations is not None:
                        for variation in variations.findall(f"{ns}Variation"):
                            sku = self._text(variation, "SKU")
                            variation_status = variation.find(f"{ns}SellingStatus")
                            variation_price, variation_currency = self._amount(
                                variation_status,
                                "CurrentPrice",
                            ) if variation_status is not None else (None, None)
                            variation_quantity = int(
                                self._text(variation, "Quantity", "0") or 0
                            )
                            variation_sold = int(
                                self._text(
                                    variation,
                                    "SellingStatus/QuantitySold",
                                    "0",
                                )
                                or 0
                            )
                            active.append({
                                "sku": sku,
                                "offerId": item_id,
                                "listing": {
                                    "listingId": item_id,
                                    "listingStatus": "ACTIVE",
                                },
                                "pricingSummary": {
                                    "price": {
                                        "currency": variation_currency or currency,
                                        "value": variation_price,
                                    }
                                },
                                "marketplaceId": "EBAY_US",
                                "availableQuantity": max(
                                    variation_quantity - variation_sold,
                                    0,
                                ),
                                "variation": True,
                            })
                    else:
                        sku = self._text(item, "SKU")
                        active.append({
                            "sku": sku,
                            "offerId": item_id,
                            "listing": {
                                "listingId": item_id,
                                "listingStatus": "ACTIVE",
                            },
                            "pricingSummary": {
                                "price": {
                                    "currency": currency,
                                    "value": price,
                                }
                            },
                            "marketplaceId": "EBAY_US",
                            "availableQuantity": max(quantity - quantity_sold, 0),
                            "variation": False,
                        })

            pagination_result = root.find(
                f"{ns}ActiveList/{ns}PaginationResult"
            )
            total_pages = int(
                self._text(
                    pagination_result,
                    "TotalNumberOfPages",
                    "1",
                )
                or 1
            ) if pagination_result is not None else 1

            if page_number >= total_pages:
                return active
            page_number += 1

    def update_price(self, offer_id, price, currency="USD", sku=None):
        inventory_status = ET.Element("InventoryStatus")
        ET.SubElement(inventory_status, "ItemID").text = str(offer_id)
        if sku:
            ET.SubElement(inventory_status, "SKU").text = sku
        ET.SubElement(inventory_status, "StartPrice").text = str(price)

        root = self._trading_request(
            "ReviseInventoryStatus",
            [inventory_status],
        )
        ns = "{urn:ebay:apis:eBLBaseComponents}"
        ack = self._text(root, "Ack", "Failure")
        if ack not in {"Success", "Warning"}:
            raise EbayError(f"eBay price update failed for item {offer_id}.")
        return root


    def create_fixed_price_listing(
        self,
        *,
        sku,
        title,
        description,
        category_id,
        price,
        quantity,
        image_url,
        item_specifics,
        condition_descriptor_value,
        postal_code="98102",
        location="Seattle, Washington",
        shipping_service="USPSFirstClass",
        shipping_cost="0.00",
        additional_shipping_cost="0.00",
    ):
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")
        if not sku:
            raise ValueError("SKU is required.")
        if not image_url or not image_url.startswith("https://"):
            raise ValueError("A valid HTTPS image URL is required.")

        item = ET.Element("Item")
        ET.SubElement(item, "Country").text = "US"
        ET.SubElement(item, "Currency").text = "USD"
        ET.SubElement(item, "Description").text = description
        ET.SubElement(item, "DispatchTimeMax").text = "1"
        ET.SubElement(item, "ListingDuration").text = "GTC"
        ET.SubElement(item, "ListingType").text = "FixedPriceItem"
        ET.SubElement(item, "Location").text = location
        ET.SubElement(item, "PostalCode").text = postal_code
        ET.SubElement(item, "Quantity").text = str(quantity)
        ET.SubElement(item, "SKU").text = sku
        ET.SubElement(item, "InventoryTrackingMethod").text = "SKU"
        ET.SubElement(item, "StartPrice").text = f"{float(price):.2f}"
        ET.SubElement(item, "CategoryMappingAllowed").text = "true"

        primary_category = ET.SubElement(item, "PrimaryCategory")
        ET.SubElement(primary_category, "CategoryID").text = str(category_id)

        ET.SubElement(item, "Title").text = title
        ET.SubElement(item, "ConditionID").text = "4000"

        condition_descriptors = ET.SubElement(item, "ConditionDescriptors")
        descriptor = ET.SubElement(condition_descriptors, "ConditionDescriptor")
        ET.SubElement(descriptor, "Name").text = "40001"
        ET.SubElement(descriptor, "Value").text = str(condition_descriptor_value)

        specifics = ET.SubElement(item, "ItemSpecifics")
        for name, value in item_specifics.items():
            if value is None or value == "":
                continue
            pair = ET.SubElement(specifics, "NameValueList")
            ET.SubElement(pair, "Name").text = str(name)
            ET.SubElement(pair, "Value").text = str(value)

        picture_details = ET.SubElement(item, "PictureDetails")
        ET.SubElement(picture_details, "PictureSource").text = "Vendor"
        ET.SubElement(picture_details, "PictureURL").text = image_url

        shipping = ET.SubElement(item, "ShippingDetails")
        ET.SubElement(shipping, "ShippingType").text = "Flat"
        option = ET.SubElement(shipping, "ShippingServiceOptions")
        ET.SubElement(option, "ShippingServicePriority").text = "1"
        ET.SubElement(option, "ShippingService").text = shipping_service
        ET.SubElement(option, "ShippingServiceCost").text = shipping_cost
        ET.SubElement(option, "ShippingServiceAdditionalCost").text = additional_shipping_cost

        return_policy = ET.SubElement(item, "ReturnPolicy")
        ET.SubElement(return_policy, "ReturnsAcceptedOption").text = "ReturnsNotAccepted"

        root = self._trading_request("AddFixedPriceItem", [item])
        ns = "{urn:ebay:apis:eBLBaseComponents}"
        item_id = self._text(root, "ItemID")
        if not item_id:
            raise EbayError("eBay created the listing but did not return an ItemID.")
        return {
            "item_id": item_id,
            "sku": self._text(root, "SKU", sku),
            "start_time": self._text(root, "StartTime"),
            "end_time": self._text(root, "EndTime"),
        }

    def update_quantity(self, item_id, quantity, sku=None):
        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        inventory_status = ET.Element("InventoryStatus")
        ET.SubElement(inventory_status, "ItemID").text = str(item_id)
        if sku:
            ET.SubElement(inventory_status, "SKU").text = sku
        ET.SubElement(inventory_status, "Quantity").text = str(quantity)

        root = self._trading_request("ReviseInventoryStatus", [inventory_status])
        ack = self._text(root, "Ack", "Failure")
        if ack not in {"Success", "Warning"}:
            raise EbayError(f"eBay quantity update failed for item {item_id}.")
        return root
