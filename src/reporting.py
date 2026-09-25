from datetime import datetime, timezone
import json
from html import escape

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

def save_report_page(report, path):
    def money(value):
        try:
            return f"${float(value):,.2f}"
        except (TypeError, ValueError):
            return escape(str(value))

    rows = "".join(
        f"<tr><td><code>{escape(str(x.get('sku','')))}</code></td><td>{money(x.get('old_price'))}</td><td>{money(x.get('new_price'))}</td></tr>"
        for x in report["changes"]
    )
    skip_rows = "".join(
        f"<tr><td><code>{escape(str(x.get('sku','')))}</code></td><td>{escape(str(x.get('reason','')))}</td></tr>"
        for x in report["skips"]
    )
    error_rows = "".join(
        f"<tr><td><code>{escape(str(x.get('sku','')))}</code></td><td>{escape(str(x.get('reason','')))}</td></tr>"
        for x in report["errors_detail"]
    )

    def section(title, headers, body):
        if not body:
            return ""
        return f"<section><h2>{title}</h2><table><thead><tr>{''.join(f'<th>{h}</th>' for h in headers)}</tr></thead><tbody>{body}</tbody></table></section>"

    mode = "DRY RUN" if report.get("dry_run", True) else "LIVE"
    environment = escape(str(report.get("environment", "unknown")).upper())
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MTG eBay Repricer</title>
<style>
body{{font-family:Arial,sans-serif;max-width:1000px;margin:auto;padding:32px 20px;line-height:1.5}}
h1{{margin-bottom:4px}} .sub{{opacity:.7}} .badge{{display:inline-block;padding:6px 10px;border-radius:6px;background:#8a6500;color:white;font-weight:bold}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0}}
.stat{{border:1px solid #777;border-radius:8px;padding:16px}} .num{{display:block;font-size:28px;font-weight:bold}}
table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #777;text-align:left;padding:9px}}
section{{margin-top:28px}} code{{font-family:monospace}}
</style></head><body>
<h1>MTG eBay Repricer</h1>
<p class="sub">Automated pricing report for Magic: The Gathering eBay listings.</p>
<p><span class="badge">{mode} | {environment}</span></p>
<p><strong>Last run:</strong> {escape(report["generated_at"])}</p>
<div class="stats">
<div class="stat"><span class="num">{report["listings_checked"]}</span>Listings Checked</div>
<div class="stat"><span class="num">{report["price_changes"]}</span>Price Changes</div>
<div class="stat"><span class="num">{report["no_changes"]}</span>No Changes</div>
<div class="stat"><span class="num">{report["skipped"]}</span>Skipped</div>
<div class="stat"><span class="num">{report["errors"]}</span>Errors</div>
</div>
{section("Price Changes",["SKU","Old Price","New Price"],rows)}
{section("Skipped Listings",["SKU","Reason"],skip_rows)}
{section("Errors",["SKU","Reason"],error_rows)}
<p><a href="privacy.html">Privacy</a> | <a href="oauth-callback.html">OAuth Callback</a></p>
</body></html>"""
    path.write_text(html, encoding="utf-8")

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
