# MTG eBay Repricer

A standalone tool for repricing Magic: The Gathering eBay listings using Scryfall pricing data.

The project is set up for any Magic: The Gathering card, regardless of set, expansion, or product line. It is not tied to Fallout or any other specific MTG release.

## Current status

The project currently contains the foundation for:

- Human-readable eBay SKUs
- Duplicate SKU detection
- Listing validation
- Scryfall price retrieval
- Configurable price calculations
- Automated tests for SKU and pricing behavior

The next major component is the eBay Inventory API integration. Scheduled execution through GitHub Actions will be added after the eBay data model and API behavior are tested.

## SKU format

`SET-CARDNUMBER-FOILTYPE-CONDITION`

Examples:

- `PIP-11-NORMAL-NM`
- `MH3-154-FOIL-LP`
- `DMU-123-NORMAL-NM`
- `SLD-796-FOIL-NM`

The set is uppercase. Collector numbers do not contain leading zeros. Finish is `NORMAL` or `FOIL`. Condition is `NM`, `LP`, `HP`, or `D`.

The SKU identifies the eBay listing. The exact Scryfall printing is stored separately using its Scryfall ID, so cards with the same name from different printings can be managed independently.

Multiple copies of the same card, printing, finish, and condition should normally be represented by one eBay listing with an appropriate quantity.

## Error handling

The program reports errors rather than silently correcting them. A problem with one listing should not prevent other valid listings from being processed.

The program will only remove a listing from its local data after eBay explicitly confirms that the corresponding listing or offer is no longer active/published. A sale that merely reduces quantity does not remove the listing.

## Pricing

Pricing rules are stored in `config.json` rather than hard-coded into the program. The default configuration currently applies a 95% multiplier to Scryfall's USD price with a $0.99 minimum price.

The pricing system is designed so the rule can be changed without modifying the source code.


## Operation

The program defaults to dry-run mode. Dry-run mode calculates proposed prices and produces a report without changing eBay.

eBay credentials are supplied through GitHub Actions secrets:
- EBAY_CLIENT_ID
- EBAY_CLIENT_SECRET
- EBAY_REFRESH_TOKEN

The scheduled workflow runs tests first, then the repricer, and uploads the generated report as a GitHub Actions artifact.

Before enabling live repricing, verify the dry-run report with real eBay credentials. Change "runtime.dry_run" in config.json to false only after that verification.

The repricer detects duplicate SKUs and malformed SKU/listing combinations and reports them instead of silently changing them.
