# API Quick Reference

All skills in this plugin use two shell scripts to call external APIs. Credentials are stored locally in `~/.claude/plugins/data/real-estate-broker/credentials.json` — set via `/setup`.

## Qobrix CRM API

**Script:** `${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh`

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" METHOD "/api/v2/ENDPOINT" '[JSON_BODY]'
```

### Common Endpoints

| Action | Method | Endpoint | Body |
|--------|--------|----------|------|
| List properties | GET | `/api/v2/properties?limit=25&page=1` | — |
| Get property | GET | `/api/v2/properties/{id}` | — |
| Create property | POST | `/api/v2/properties` | `{"name":"...","property_type":"apartment",...}` |
| Update property | PUT | `/api/v2/properties/{id}` | `{"status":"available"}` |
| Search properties | GET | `/api/v2/properties?search=status%20%3D%3D%20%22available%22` | — |
| List contacts | GET | `/api/v2/contacts?limit=25` | — |
| Get contact | GET | `/api/v2/contacts/{id}` | — |
| Create contact | POST | `/api/v2/contacts` | `{"first_name":"...","last_name":"..."}` |
| Update contact | PUT | `/api/v2/contacts/{id}` | `{...fields...}` |
| List opportunities | GET | `/api/v2/opportunities?limit=25` | — |
| Get opportunity | GET | `/api/v2/opportunities/{id}` | — |
| Create opportunity | POST | `/api/v2/opportunities` | `{"contact_name":"<contact-uuid>","enquiry_type":"apartment","buy_rent":"to_buy","source":"direct","status":"new"}` |
| Update opportunity | PUT | `/api/v2/opportunities/{id}` | `{"status":"viewing"}` |
| List tasks | GET | `/api/v2/tasks?limit=25` | — |
| Create task | POST | `/api/v2/tasks` | `{"title":"...","due_date":"..."}` |
| Update task | PUT | `/api/v2/tasks/{id}` | `{"status":"completed"}` |
| Get activity log | GET | `/api/v2/activity-logs?related_to={id}&limit=10` | — |
| Current user info | GET | `/api/v2/users/self` | — |
| Lookup location | GET | `/api/v2/locations?search={query}` | — |
| Upload media | POST | `/api/v2/properties/{id}/media` | `{"url":"...","category":"photos"}` |

### Search/Filter Syntax

Pass search expressions via URL-encoded `search` query parameter:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET \
  '/api/v2/properties?search=status%20%3D%3D%20%22available%22%20and%20property_type%20%3D%3D%20%22apartment%22&limit=25'
```

**Operators:** `==`, `!=`, `>`, `>=`, `<`, `<=`, `contains`, `is null`, `is not null`, `in`, `not in`
**Logic:** `and`, `or`
**Variables:** `CURRENT_USER`, `TODAY`, `YESTERDAY`, `THIS_WEEK`, `THIS_MONTH`

### Pagination

All list endpoints support `?limit=N&page=N`. Default limit is 25, max 100.

### Enum Values (verified against live API)

**Property fields:**
- `sale_rent`: `for_sale`, `for_rent`, `for_sale_and_rent`
- `property_type` / `type`: `apartment`, `house`, `land`, `office`, `retail`, `industrial`, `investment`, `other`
- `furnished`: `furnished`, `semi_furnished`, `optionally_furnished`, `unfurnished`
- `status` (property): `available`, `sold`, `rented`, `under_offer`, `withdrawn`
- `construction_year`: integer (NOT `year_built`)

**Opportunity fields:**
- `contact_name`: UUID of the related contact (NOT `contact_id`)
- `status` (NOT `stage`): `new`, `assigned`, `informative`, `proposal`, `viewing`, `negotiation`, `closed_won`, `closed_lost`
- `source` (fixed enum — only these two): `direct`, `agent`
- `buy_rent`: `to_buy`, `to_rent`
- `enquiry_type`: matches property types (`apartment`, `house`, `land`, etc.)
- `construction_stage`: `completed`, `under_construction`, `off_plan`

**Tips:**
- To expand the contact on an opportunity, use `?include[]=ContactNameContacts`
- `virtual_contact_name` is a read-only display field — don't send it in POST/PUT
- `ref` is an auto-generated integer reference number — don't set it on create

---

## WaSender WhatsApp API

**Script:** `${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh`

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" METHOD "/api/ENDPOINT" '[JSON_BODY]'
```

### Common Endpoints

| Action | Method | Endpoint | Body |
|--------|--------|----------|------|
| Send text | POST | `/api/send-message` | `{"to":"35799123456","text":"Hello!"}` |
| Send image | POST | `/api/send-image` | `{"to":"35799123456","url":"https://...","caption":"..."}` |
| Send location | POST | `/api/send-location` | `{"to":"35799123456","lat":34.7,"lng":33.0,"name":"..."}` |
| Upload media (base64) | POST | `/api/upload` | `{"base64":"data:image/jpeg;base64,..."}` |
| Session status | GET | `/api/status` | — |
| Get messages | GET | `/api/messages?limit=20` | — |

### Phone Number Format

Always use international format without `+` prefix: `35799123456` (Cyprus example).

### Sending Images from Base64 or Local Files

`/api/send-image` only accepts a public HTTPS URL. When the source is base64 (or a local file you base64-encode), upload it to `/api/upload` first — the response returns `publicUrl` (valid 24h) which you then pass to `/api/send-image`.

```bash
# Upload (JSON/base64 method — works with the existing wasender-api.sh script)
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" POST "/api/upload" \
  '{"base64":"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQE..."}'
# -> {"success":true,"publicUrl":"https://wasenderapi.com/media/<uuid>.jpg"}

# Then send
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" POST "/api/send-image" \
  '{"to":"35799123456","url":"https://wasenderapi.com/media/<uuid>.jpg","caption":"..."}'
```

MIME can be embedded in the Data URL prefix (`data:<mime>;base64,...`) or passed separately as `"mimetype":"image/jpeg"`. Size limits: images 16 MB, videos 50 MB, audio 16 MB, documents 100 MB, stickers (webp) 5 MB. Files are validated by magic numbers against the declared MIME.

---

## Error Handling

Both scripts exit with code 1 and print JSON to stderr if credentials are missing. Check for:
- `"error":"not_configured"` — reinstall the plugin or update plugin config
- HTTP 401/403 — API key is wrong or expired
- HTTP 404 — wrong endpoint or ID
- HTTP 422 — validation error, check required fields
- HTTP 429 — rate limited, wait and retry
