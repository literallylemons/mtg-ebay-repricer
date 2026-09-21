from datetime import datetime, timezone
import json

def build_report():
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "listings_checked": 0,
        "price_changes": 0,
        "no_changes": 0,
        "skipped": 0,
        "errors": 0,
        "changes": [],
        "skips": [],
        "errors_detail": [],
    }

def save_report(report, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

def print_report(report):
    print("MTG eBay Repricer Report")
    print("Generated: " + report["generated_at"])
    print("Listings checked: " + str(report["listings_checked"]))
    print("Price changes: " + str(report["price_changes"]))
    print("No changes: " + str(report["no_changes"]))
    print("Skipped: " + str(report["skipped"]))
    print("Errors: " + str(report["errors"]))
    if report["changes"]:
        print("\nPRICE CHANGES")
        for change in report["changes"]:
            print("- " + change["sku"] + ": $" + change["old_price"] + " -> $" + change["new_price"])
    if report["skips"]:
        print("\nSKIPPED")
        for skip in report["skips"]:
            print("- " + skip["sku"] + ": " + skip["reason"])
    if report["errors_detail"]:
        print("\nERRORS")
        for error in report["errors_detail"]:
            print("- " + error["sku"] + ": " + error["reason"])
