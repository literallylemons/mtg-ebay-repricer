import os
from pathlib import Path
import json

from src.ebay import EbayClient
from src.repricer import build_repricing_plan, load_config
from src.reporting import build_report, print_report, save_report


def load_local_listings():
    path = Path("data/listings.json")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    config = load_config()
    report = build_report()
    dry_run = config["runtime"].get("dry_run", True)
    environment = os.environ.get("EBAY_ENVIRONMENT", "production")

    has_credentials = all(
        os.environ.get(name)
        for name in ("EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET", "EBAY_REFRESH_TOKEN")
    )

    if has_credentials:
        client = EbayClient(environment)
        offers = client.get_active_offers()
    elif dry_run:
        print("No eBay credentials found. Using local listings fixture.")
        offers = load_local_listings()
        client = None
    else:
        raise RuntimeError("eBay credentials are required when dry_run is false.")

    plan = build_repricing_plan(offers, config)
    report["listings_checked"] = len(offers)
    report["price_changes"] = len(plan["updates"])
    report["no_changes"] = len(plan["no_changes"])
    report["skipped"] = len(plan["skips"])
    report["errors"] = len(plan["errors"])
    report["changes"] = plan["updates"]
    report["skips"] = plan["skips"]
    report["errors_detail"] = plan["errors"]

    if not dry_run and client and plan["updates"]:
        for update in plan["updates"]:
            client.update_price(update["offer_id"], update["new_price"], update["currency"])

    if dry_run:
        print("\nDRY RUN: no eBay prices were changed.")

    report_path = Path("reports/latest.json")
    save_report(report, report_path)
    print_report(report)


if __name__ == "__main__":
    main()
