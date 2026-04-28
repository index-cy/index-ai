---
name: qobrix-price-updater
description: |
  Update property listings in Qobrix CRM from developer PDF price lists. Use this skill whenever the user uploads a PDF price list (or mentions a price list, прайс-лист, cennik) and wants to update Qobrix/Cobrix CRM with the latest prices, statuses, and inspection dates. Also trigger when the user says "обнови CRM", "update properties", "загрузи прайс", "прайс-лист", or mentions syncing developer data with CRM. This skill handles the full workflow: parsing the PDF, finding the project in Qobrix, matching units, and updating status, price, and inspection date for each unit.
version: 1.0.0
---

# Qobrix Price List Updater

This skill takes a developer's PDF price list and updates the corresponding property listings in Qobrix CRM. It handles PDF parsing, project lookup, unit matching, and batch updates — all through the Qobrix REST API using **PATCH** for updates.

## Prerequisites

Credentials are read from the plugin credentials file at
`$CLAUDE_DIR/plugins/data/real-estate-broker/credentials.json` (the same file used by `scripts/qobrix-api.sh`). If the helper scripts return `"error":"not_configured"`, tell the user to run `/setup`.

## Workflow

### Step 1: Parse the PDF

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-price-updater/parse_pdf.py" "<path-to-pdf>"
```

Output JSON contains:
- `project_name` — title from PDF header
- `date` — date from PDF
- `units` — array of `{unit_number, type, area, price, status, status_raw}`

PDF status mapping:
- `SOLD` → `sold`
- `RESERVED` → `reserved`
- `FOR SALE` / `AVAILABLE` → `available`
- `UNDER OFFER` → `under_offer`
- `RENTED` → `rented`

If `parse_pdf.py` fails, fall back to manual PDF reading (pdfplumber or the pdf skill) and extract project name + per-row unit number, price, status.

### Step 2: Find the project in Qobrix

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-price-updater/qobrix_api.py" search-project "<project-name>"
```

Project names in CRM often differ from the PDF (e.g., "PARAMOUNT" in PDF → "MITO Paramount" in CRM). The script uses `name contains` search.

- **Multiple matches** — present them and ask which is correct.
- **No match** — try shorter/partial names, then optionally add `--developer "<dev-name>"`.
- **Still no match** — ask the user for the project UUID directly.

### Step 3: List existing units

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-price-updater/qobrix_api.py" list-units "<project-uuid>"
```

Returns all properties where `project == "<uuid>"` with `unit_number`, `status`, `list_selling_price_amount`, `inspection_date`.

### Step 4: Match and update units

For each PDF unit, find the property by matching `unit_number`, then:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-price-updater/qobrix_api.py" update-property "<property-uuid>" \
  --status "<new-status>" \
  --price "<new-price>" \
  --inspection-date "<YYYY-MM-DD>"
```

The script issues an HTTP **PATCH** to `/api/v2/properties/{id}`. The `inspection_date` field is sent in the full datetime form `YYYY-MM-DDT00:00:00+00:00` (the `Z` suffix is silently dropped by Qobrix, so we never use it). Use today's date as the inspection date — it represents when the price list was last verified.

### Step 5: Report results

Show the user a summary table:
- Unit number
- Old status → New status
- Old price → New price
- Success / failure

Flag PDF units NOT found in CRM, and CRM units NOT in the PDF.

## Important notes

- Always confirm with the user before applying updates — show a preview.
- If a PDF unit isn't in the CRM, ask whether to skip or create.
- Don't change `plus_vat` unless the user asks.
- If the developer name is unclear, ask before searching.

## Error handling

- `"error":"not_configured"` → user runs `/setup`.
- 401/403 → tell user to verify credentials in `/setup`.
- 429 → script retries with exponential backoff automatically.
- Per-unit failure → log and continue, report all failures at the end.
