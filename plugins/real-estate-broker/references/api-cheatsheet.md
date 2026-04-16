# API Quick Reference

All skills in this plugin use two shell scripts to call external APIs. Credentials are automatically injected by Claude Code from the `userConfig` defined in `plugin.json` — they're set during plugin installation.

## coWork CRM API

**Script:** `${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh`

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" METHOD "/api/v2/ENDPOINT" '[JSON_BODY]'
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
| Create opportunity | POST | `/api/v2/opportunities` | `{"name":"...","contact_id":"..."}` |
| Update opportunity | PUT | `/api/v2/opportunities/{id}` | `{"stage":"viewing"}` |
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
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" GET \
  '/api/v2/properties?search=status%20%3D%3D%20%22available%22%20and%20property_type%20%3D%3D%20%22apartment%22&limit=25'
```

**Operators:** `==`, `!=`, `>`, `>=`, `<`, `<=`, `contains`, `is null`, `is not null`, `in`, `not in`
**Logic:** `and`, `or`
**Variables:** `CURRENT_USER`, `TODAY`, `YESTERDAY`, `THIS_WEEK`, `THIS_MONTH`

### Pagination

All list endpoints support `?limit=N&page=N`. Default limit is 25, max 100.

### Enum Values

**sale_rent:** `for_sale`, `for_rent`, `for_sale_and_rent`
**property_type:** `apartment`, `house`, `land`, `office`, `retail`, `industrial`, `investment`, `other`
**furnished:** `furnished`, `semi_furnished`, `optionally_furnished`, `unfurnished`
**status:** `available`, `under_offer`, `sold`, `rented`, `withdrawn`
**opportunity stages:** `new`, `contacted`, `viewing`, `offer`, `negotiation`, `closed_won`, `closed_lost`

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
| Session status | GET | `/api/status` | — |
| Get messages | GET | `/api/messages?limit=20` | — |

### Phone Number Format

Always use international format without `+` prefix: `35799123456` (Cyprus example).

---

## Error Handling

Both scripts exit with code 1 and print JSON to stderr if credentials are missing. Check for:
- `"error":"not_configured"` — reinstall the plugin or update plugin config
- HTTP 401/403 — API key is wrong or expired
- HTTP 404 — wrong endpoint or ID
- HTTP 422 — validation error, check required fields
- HTTP 429 — rate limited, wait and retry
