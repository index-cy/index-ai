---
name: import-listing
description: >
  Import a property listing from a URL into coWork CRM. Use when the user says
  "import this listing", "add this property from bazaraki", "import from index",
  "add this buysellcyprus listing", "scrape this property", "import listing",
  pastes a URL from bazaraki.com, index.cy, or buysellcyprus.com, or wants to
  create a property in the CRM from an external listing.
version: 1.0.0
---

# Import Listing from URL

Scrape a property listing from a URL and create it in coWork CRM with correct field mapping, including automatic location UUID resolution, seller/agency linking, and photo upload.

## API Access

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" METHOD "/api/v2/ENDPOINT" '[BODY]'
```

If the script returns `"error":"not_configured"`, tell the user to reinstall the plugin or check their plugin configuration.

## Supported Sites

| Site | URL Pattern | Notes |
|------|------------|-------|
| Bazaraki | `bazaraki.com/adv/...` | Largest Cyprus classifieds |
| Index.cy | `index.cy/sale/...` or `index.cy/rent/...` | Real estate portal |
| BuySellCyprus | `buysellcyprus.com/...` | Property marketplace |
| Other | Any property listing URL | Best effort extraction |

## Step 1: Extract Listing Data

Use WebFetch to retrieve the listing page. Extract these fields:

| Listing Field | coWork Field | Type | Notes |
|--------------|-------------|------|-------|
| Title/Name | `name` | string | Required |
| Sale price | `list_selling_price_amount` | float | Numeric only, no currency |
| Rental price | `list_rental_price_amount` | float | Numeric only |
| Bedrooms | `bedrooms` | integer | |
| Bathrooms | `bathrooms` | integer | |
| Covered area | `covered_area_amount` | float | sqm |
| Plot area | `plot_area_amount` | float | sqm, for houses/land |
| For sale or rent | `sale_rent` | enum | See values below |
| Property type | `property_type` | enum code | See values below |
| City/Area | location lookup | string | Used to find location UUID |
| Floor | `floor_number` | integer | |
| Year built | `year_built` | integer | |
| Furnished | `furnished` | enum | See values below |
| Description | `description` | string | Full text + source attribution |
| Status | `status` | enum | Always set to `available` |
| Agency/Seller | contact lookup | string | Used to find/create seller |
| Image URLs | media upload | array | Upload after property creation |

## Step 2: Resolve Location UUID

coWork requires a location UUID, not a plain text city name.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" GET "/api/v2/locations?search={district}%20{area}"
```

If no exact match, try: fuzzy match on area, match on district only, or ask the user.

## Step 3: Map Enum Values

### `sale_rent`
| Listing text | coWork value |
|-------------|-------------|
| For sale / buy | `for_sale` |
| For rent / to let | `for_rent` |
| Both | `for_sale_and_rent` |

### `property_type`
| Listing text | coWork code |
|-------------|------------|
| Apartment / Flat | `apartment` |
| House / Detached / Villa | `house` |
| Land / Plot | `land` |
| Office | `office` |
| Shop / Retail | `retail` |
| Commercial / Industrial | `industrial` |
| Investment | `investment` |
| Other | `other` |

### `furnished`
| Listing text | coWork value |
|-------------|-------------|
| Fully furnished | `furnished` |
| Semi / partly | `semi_furnished` |
| Optional / negotiable | `optionally_furnished` |
| Unfurnished / empty | `unfurnished` |

## Step 4: Present Summary for Confirmation

Before creating, show the user:

```
Property to import:
---
Name:        3 Bedroom Apartment in Mesa Geitonia, Limassol
Type:        apartment (for_sale)
Price:       EUR 375,000
Beds/Baths:  3 bed / 1 bath
Area:        99m2 covered
Floor:       1st
Built:       1997
Location:    Mesa Geitonia, Limassol [matched UUID]
Agency:      Kazo Real Estate [found in contacts]
Images:      7 photos found

Source: https://index.cy/sale/9140726-...
---
Create in coWork?
```

Wait for confirmation.

## Step 5: Create Property

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" POST "/api/v2/properties" \
  '{"name":"...","property_type":"apartment","sale_rent":"for_sale","list_selling_price_amount":375000,"bedrooms":3,"bathrooms":1,"covered_area_amount":99,"location":"{location_uuid}","status":"available","description":"..."}'
```

Always include in `description`:
```
{original description text}

---
Imported from {Site Name}
Source URL: {original_url}
External reference: {ref_number_if_found}
Import date: {today}
Original agency: {agency_name_if_found}
```

## Step 5.5: Link Seller/Agency Contact

After creating, look up the listing agency:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" GET "/api/v2/contacts?search=first_name%20contains%20%22{agency_name}%22&limit=5"
```

If not found, create:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" POST "/api/v2/contacts" '{"first_name":"{agency_name}","is_company":true}'
```

Then link:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" PUT "/api/v2/properties/{id}" '{"seller":"{contact_uuid}"}'
```

## Step 5.6: Upload Photos

For each image URL:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" POST "/api/v2/properties/{id}/media" \
  '{"url":"{image_url}","display_order":{N},"category":"{featured_photo|photos}"}'
```

First image: `category="featured_photo"`, rest: `category="photos"`.

If upload fails with permission error, collect all URLs and show them for manual upload.

## Step 6: Report Result

```
Created in coWork: #{id} — {title}
Open: {crm_url}/properties/view/{id}

Seller:  {agency} [linked]
Photos:  7/7 uploaded
```

Then offer:
- "Link this property to an opportunity?"
- "Send this to a customer on WhatsApp?"
- "Import another listing?"

## Bulk Import

If given multiple URLs, process each and show a results table at the end.

## Error Handling

- **Page fetch fails**: ask user to paste listing details manually
- **Location not found**: show closest matches, ask user to confirm
- **Missing required fields**: ask user to fill in name or property_type
- **Duplicate detected**: warn if same name + location + price exists
- **Image upload permission denied**: collect URLs, show in report for manual upload
