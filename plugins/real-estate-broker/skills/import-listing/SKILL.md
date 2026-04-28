---
name: import-listing
description: >
  Import a property listing from a URL into Qobrix CRM. Use when the user says
  "import this listing", "add this property from bazaraki", "import from index",
  "add this buysellcyprus listing", "scrape this property", "import listing",
  "переноси с Базараки", "импорт листинга",
  pastes a URL from bazaraki.com, index.cy, or buysellcyprus.com, or wants to
  create a property in the CRM from an external listing.
version: 1.0.0
---

# Import Listing from URL

Scrape a property listing from a URL and create it in Qobrix CRM with correct field mapping, including automatic location UUID resolution, seller/agency linking, and photo upload.

## API Access

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" METHOD "/api/v2/ENDPOINT" '[BODY]'
```

If the script returns `"error":"not_configured"`, tell the user to run `/setup` to configure their API credentials.

## Supported Sites

| Site | URL Pattern | Notes |
|------|------------|-------|
| Bazaraki | `bazaraki.com/adv/...` | Largest Cyprus classifieds |
| Index.cy | `index.cy/sale/...` or `index.cy/rent/...` | Real estate portal |
| BuySellCyprus | `buysellcyprus.com/...` | Property marketplace |
| Other | Any property listing URL | Best effort extraction |

## Step 1: Extract Listing Data

Use WebFetch to retrieve the listing page. Extract these fields:

| Listing Field | Qobrix Field | Type | Notes |
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
| Area/Town | `city` | string | E.g. "Sotiros", "Mesa Geitonia" |
| District | `state` | string | E.g. "Larnaca", "Limassol" |
| Country code | `country` | string | ISO-2, e.g. `CY` |
| Street address | `street` | string | Full street name + number if shown |
| Postal code | `post_code` | string | ZIP / postcode if shown |
| Lat,Lng | `coordinates` | string | Format: `"34.9225,33.6210"` |
| Floor | `floor_number` | integer | |
| Year built | `year_built` | integer | |
| Furnished | `furnished` | enum | See values below |
| Description | `description` | string | Full text + source attribution. Run through cleanup patterns (see references/description-cleanup-patterns.md) |
| Status | `status` | enum | Always set to `available` |
| Agency/Seller | contact lookup | string | Used to find/create seller |
| Image URLs | media upload | array | Upload after property creation |
| Internal area | `internal_area_amount` | float | sqm — extract when present |
| Total area | `total_area_amount` | float | sqm — extract when present |
| Air conditioning | `air_condition` | bool | Extract when listed |
| Elevator | `elevator` | bool | |
| Private pool | `private_swimming_pool` | bool | |
| Common pool | `common_swimming_pool` | bool | |
| New build | `new_build` | bool | True for off-plan / newly built |
| Covered parking | `covered_parking` | bool | |
| Uncovered parking | `uncovered_parking` | bool | |

### Mandatory Cyprus default fields

When the source listing is in Cyprus (`country=CY`), these fields must ALWAYS be populated, regardless of whether the source provides them:

| Field | Value | Notes |
|-------|-------|-------|
| `price_qualifier` | `"fixed"` | Qobrix enum value for Fixed Price |
| `geocode_type` | `"exact"` | Qobrix enum value for Set |
| `energy_efficiency_grade` | from listing, else `"h"` | `h` is the lowest grade — use when source has no energy data |
| `inspection_date` | `{listing_date}` or today, full datetime `YYYY-MM-DDT00:00:00+00:00` | Datetime field — never use `Z` suffix (Qobrix silently drops it) |

## Step 2: Resolve Location UUID AND Address Fields

Qobrix stores location in **two complementary ways** — both must be populated:

1. **`location` UUID** — links to the Qobrix locations tree (district/area hierarchy).
2. **Free-text address fields** — `street`, `post_code`, `city`, `state`, `country`, `coordinates`. These are what show on the property "Location" page. If you only set `location` + `coordinates`, Street and Post Code display as "--".

### 2a. Look up the location UUID
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/locations?search={district}%20{area}"
```
If no exact match, try: fuzzy match on area, match on district only, or ask the user.

### 2b. Extract the street address and postal code from the listing page
Scrape hard for these — they are often tucked into the "Location" / "Address" section, the breadcrumb, or the embedded Google Maps block:
- **Street** — full street name, plus number if displayed. If the listing only gives a neighbourhood name, put that in `city` (not `street`) and leave `street` null.
- **Postal code** — Cyprus postcodes are 4 digits (e.g. `6046`, `7550`). Look for them near the address, in structured data (JSON-LD), or in the map iframe URL (`&q=...%206046`).
- **Coordinates** — Extract from the map embed (`q=lat,lng` or `center=lat,lng`). Format as `"lat,lng"` string.
- **City / State / Country** — From breadcrumbs or title (e.g. "Larnaca → Sotiros" → `state=Larnaca`, `city=Sotiros`, `country=CY`).

If street or post_code cannot be found on the page, leave them null — don't invent values.

## Step 3: Map Enum Values

### `sale_rent`
| Listing text | Qobrix value |
|-------------|-------------|
| For sale / buy | `for_sale` |
| For rent / to let | `for_rent` |
| Both | `for_sale_and_rent` |

### `property_type`
| Listing text | Qobrix code |
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
| Listing text | Qobrix value |
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
Street:      Agias Fylaxeos 128
Post Code:   3025
Coordinates: 34.6892,33.0411
Agency:      Kazo Real Estate [found in contacts]
Images:      7 photos found

Source: https://index.cy/sale/9140726-...
---
Create in Qobrix?
```

Wait for confirmation.

## Step 5: Create Property

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/properties" \
  '{"name":"...","property_type":"apartment","sale_rent":"for_sale","list_selling_price_amount":375000,"bedrooms":3,"bathrooms":1,"covered_area_amount":99,"internal_area_amount":99,"total_area_amount":110,"location":"{location_uuid}","street":"{street}","post_code":"{postcode}","city":"{area}","state":"{district}","country":"CY","coordinates":"{lat},{lng}","status":"available","price_qualifier":"fixed","geocode_type":"exact","energy_efficiency_grade":"h","inspection_date":"2026-04-27T00:00:00+00:00","air_condition":true,"elevator":true,"private_swimming_pool":false,"common_swimming_pool":true,"new_build":false,"covered_parking":true,"uncovered_parking":false,"description":"..."}'
```

For Cyprus listings, always include `price_qualifier`, `geocode_type`, `energy_efficiency_grade`, and `inspection_date` — see the "Mandatory Cyprus default fields" section above.

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
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/contacts?search=first_name%20contains%20%22{agency_name}%22&limit=5"
```

If not found, create:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/contacts" '{"first_name":"{agency_name}","is_company":true}'
```

Then link:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" PUT "/api/v2/properties/{id}" '{"seller":"{contact_uuid}"}'
```

## Step 5.6: Upload Photos

### Primary path (URL-based JSON upload)

For each image URL, POST the URL to the property's media endpoint:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/properties/{id}/media" \
  '{"url":"{image_url}","display_order":{N},"category":"{featured_photo|photos}"}'
```

First image: `category="featured_photo"`, rest: `category="photos"`. Qobrix uses **separate categories** for the featured/hero image vs. the gallery — uploading only to `photos` will leave the property card thumbnail blank, so the first image must be uploaded once as `featured_photo` and (optionally) again as `photos[0]`.

### Fallback: multipart upload to `/api/v2/media`

If the URL-based upload fails (CDN blocks Qobrix's fetcher, or the response says the URL is unreachable), fall back to fetching the image bytes yourself and uploading via multipart `POST /api/v2/media`:

```
POST /api/v2/media
Content-Type: multipart/form-data
Fields:
  file          = <binary>
  category_id   = <uuid for featured_photo or photos>
  related_model = "Properties"
  related_id    = <property uuid>
  media_type    = "upload"   # required — without it the API returns 400
```

Look up category UUIDs once via:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/media/categories?search=related_model%3D%3D%27Properties%27"
```

Upload first image with the `featured_photo` category, the rest with the `photos` category. Verify success: the property's `media[]` should contain one entry where `category.name === "featured_photo"`.

### Bazaraki / cross-origin image fetch (CORS proxy)

Bazaraki's CDN (`cdn1.bazaraki.com`) and several other portals do **not** serve CORS headers, which breaks `fetch()` from a browser tab and taints canvas exports. When WebFetch can't return binary image bytes (e.g., 403 from CDN, sandbox proxy block), route the fetch through:

```
https://api.codetabs.com/v1/proxy?quest=<encoded image URL>
```

Notes:
- Rate-limited per IP (~50–100 requests). When throttled it returns HTTP 200 with a 0-byte body — always check `blob.size > 0` and skip empty responses.
- Add ~500ms delay between requests to reduce throttling.
- Other proxies tested and confirmed broken for Bazaraki: `corsproxy.io`, `thingproxy`, `cors.sh`, `corsproxy.org`, `cors.lol`, `allorigins.win`, `wsrv.nl` — don't bother retrying with these.

### Watermark removal pipeline (Bazaraki and similar portals)

Bazaraki adds a small semi-transparent "bazaraki" text watermark in the bottom-left corner. Other portals may place watermarks elsewhere.

**Default: 8% canvas crop (fast, free, no key needed).** Crop 8% from top and bottom of every gallery image — the watermark always lives in the margin and the visual loss is negligible:

```javascript
const cropPercent = 0.08;
const cropTop = Math.round(img.naturalHeight * cropPercent);
const newHeight = img.naturalHeight - cropTop * 2;
const canvas = document.createElement('canvas');
canvas.width = img.naturalWidth;
canvas.height = newHeight;
canvas.getContext('2d').drawImage(
  img, 0, cropTop, img.naturalWidth, newHeight, 0, 0, img.naturalWidth, newHeight
);
const jpegBlob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', 0.92));
```

Do this BEFORE uploading to Qobrix. Use this as the default for every Bazaraki import.

**Optional: fal.ai Flux Pro Fill (AI inpainting).** For portals with centered or tiled watermarks where cropping would cost too much content, the user can enable AI-based inpainting if they have a `FAL_KEY` set. Generate a watermark mask with OpenCV (grayscale → 41x41 Gaussian blur → subtract → threshold at 10 → dilate corner regions 7×7 ×3 iters, edge regions 5×5 ×3 iters), then call:

```python
fal_client.subscribe("fal-ai/flux-pro/v1/fill", arguments={
    "image_url": image_data_url,
    "mask_url": mask_data_url,
    "prompt": "clean wall, ceiling, floor, natural interior real estate photograph, no text, no watermark",
    "num_images": 1, "seed": 42,
})
```

Cost ≈ $0.05/megapixel. **The OpenCV mask approach is documented for completeness but is NOT required** — skip it entirely unless the user asks for AI inpainting. The 8% crop covers Bazaraki on its own. A pure-OpenCV inpaint (`cv2.inpaint(img, mask, 7, cv2.INPAINT_TELEA)`) is a free fallback when fal.ai isn't available.

If all upload paths fail, collect the cleaned image URLs and show them to the user for manual upload.

## Step 6: Report Result

```
Created in Qobrix: #{id} — {title}
Open: {crm_url}/properties/view/{id}

Seller:  {agency} [linked]
Photos:  7/7 uploaded
```

Then offer:
- "Link this property to an opportunity?"
- "Send this to a customer on WhatsApp?"
- "Import another listing?"

## Description Cleanup

Before saving the description into Qobrix, run it through the cleanup patterns documented in **`references/description-cleanup-patterns.md`** (relative to the plugin root). The patterns cover EN/RU/GR phrases — for example:

- EN: "We are pleased to present", "for sale", "call now", "by owner", "no agents"
- RU: "Имеется возможность", "Представляем", "продается", "от собственника", "торг"
- GR: "Παρουσιάζουμε", "πωλείται", "χωρίς μεσίτη"

Also strip phone numbers, emails, WhatsApp/Viber/Telegram references, and Bazaraki/Index.cy/BuySellCyprus footer/portal references. Keep all factual property info ("sea view", "walking distance to beach" stay).

After cleanup, append the source-attribution block (see Step 5).

## Bulk Import

If given multiple URLs, process each and show a results table at the end.

## Error Handling

- **Page fetch fails**: ask user to paste listing details manually
- **Location not found**: show closest matches, ask user to confirm
- **Missing required fields**: ask user to fill in name or property_type
- **Duplicate detected**: warn if same name + location + price exists
- **Image upload permission denied**: collect URLs, show in report for manual upload
