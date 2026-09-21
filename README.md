# MTG eBay Repricer

A standalone tool for repricing Magic: The Gathering eBay listings using Scryfall pricing data.

## Current status

The project currently contains the foundation for:

- Human-readable eBay SKUs
- Duplicate SKU detection
- Listing validation
- Scryfall price retrieval
- Configurable price calculations

eBay integration and scheduled execution will be added after the local data model is tested.

## SKU format

`SET-CARDNUMBER-FOILTYPE-CONDITION`

Examples:

- `PIP-11-NORMAL-NM`
- `PIP-11-FOIL-NM`
- `SLD-796-FOIL-NM`

The set is uppercase. Collector numbers do not contain leading zeros. Finish is `NORMAL` or `FOIL`. Condition is `NM`, `LP`, `HP`, or `D`.

The program reports errors rather than silently correcting them.
