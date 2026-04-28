---
name: active-leads
description: |
  Check agent leads inactivity in Qobrix CRM. Use when the user says "/active-leads", "/active-leads {agent}", "check leads", "check agent leads", "проверь лиды", "stale leads", "inactive leads", "who has stale leads", or wants to see which agents have inactive opportunities. Supports checking all agents or a specific one by email/key. Optionally delivers the report via WhatsApp through WaSender.
version: 1.0.0
---

# Active Leads — Qobrix Agent Inactivity Monitor

Monitor real-estate agents' active opportunities in Qobrix CRM and surface leads that have gone stale (inactivity 7+ days, with severity buckets and high-budget flagging).

## Triggers

- `/active-leads` — check all active agents discovered from Qobrix
- `/active-leads {agent_key_or_email}` — single agent (e.g. `/active-leads denis@…` or `/active-leads DB`)
- "проверь лиды", "stale leads", "inactive leads", "check agent leads"

## API Access

Use the plugin wrappers — no extra credentials file:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" METHOD "/api/v2/PATH" '[BODY]'
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" METHOD "/api/PATH" '[BODY]'
```

If either script returns `"error":"not_configured"`, tell the user to run `/setup`.

A small convenience wrapper is available at `${CLAUDE_PLUGIN_ROOT}/scripts/active-leads/check.sh` for quickly listing users — see "Helper script" below.

## Workflow

### Step 1: Discover active agents (no hardcoded list)

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/users?limit=100"
```

From the response `data[]`, keep users that look like real-estate agents:
- `is_active == true` (or absent), AND
- not service/system accounts (skip names matching `system`, `bot`, `integration`, etc.)

Build a map of `{id, name, email}` for the run. Cache it in memory for the rest of the session.

If the user passed an argument:
- If it looks like an email → match `email` exactly.
- If it looks like a 2-letter key (e.g. "DB") → match the initials of `name` (first letter of first + last word).
- If it's a UUID → use directly.
- Otherwise → match `name` containing the argument (case-insensitive); if multiple, ask which one.

### Step 2: Pull each agent's active opportunities

For each agent UUID:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET \
  '/api/v2/opportunities?search=owner%20%3D%3D%20%22{user_id}%22%20and%20status%20in%20%5B%22new%22%2C%22assigned%22%2C%22informative%22%2C%22proposal%22%2C%22viewing%22%2C%22negotiation%22%5D&limit=200'
```

Search expression (URL-decoded for clarity):
```
owner == "{user_id}" and status in ["new","assigned","informative","proposal","viewing","negotiation"]
```

These are the verified active Qobrix opportunity statuses. Use **`status`** (not `stage`). Closed states (`closed_won`, `closed_lost`) are excluded.

### Step 3: Compute inactivity per opportunity

Inactivity is computed from the opportunity's **`modified`** field (the last-modified timestamp). For each active opportunity:

```
inactive_days = floor((now - modified) / 1 day)
```

Bucket each opportunity (configurable — adjust the constants below if requirements change):

| Bucket | Range | Meaning |
|--------|-------|---------|
| CRITICAL | 300+ days | Practically dead, escalate |
| WARNING | 100–299 days | Long-stale, urgent attention |
| ATTENTION | 30–99 days | Needs follow-up soon |
| RECENT | 7–29 days | On the radar but slipping |

Anything < 7 days is healthy and excluded from the report.

### Step 4: Flag high-budget leads

Mark leads as **high-budget** (configurable thresholds):
- **Buy** (`buy_rent == "to_buy"`): `list_selling_price_from >= 400000` EUR
- **Rent** (`buy_rent == "to_rent"`): `list_rental_price_from >= 4000` EUR/month

Also call out separately any opportunities stuck in `negotiation` regardless of bucket.

### Step 5: Build the report (per agent)

```
{Agent Name}: {N} active leads inactive 7+ days

CRITICAL (X, 300+ days):
  {contact_name} — {Xd} | {status} | {buy_rent} | ref:{ref} [Buy 400K-500K]

WARNING (X, 100-299 days):
  ...

ATTENTION (X, 30-99 days):
  ...

RECENT (X, 7-29 days):
  ...

Summary: {N} of {M} active leads need attention
{X} high-budget leads inactive
{X} leads stuck in negotiation
```

Note: in Qobrix opportunities, `contact_name` is a UUID (link to a contact). If you need the human-readable contact name, follow it with a `GET /api/v2/contacts/{uuid}` lookup, or use the expanded contact name from the opportunity payload if available.

### Step 6: Deliver

**Default — print summary in chat.** Show each agent's report block plus a top-line count across all agents.

**Optional — WhatsApp delivery.** If the user provides a phone number (or asks to "send to WhatsApp +35799..."), send each agent's block as a separate WhatsApp message:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" POST "/api/send-message" \
  '{"to":"35799123456","text":"<agent block here>"}'
```

If WaSender returns `"error":"not_configured"`, ask the user to run `/setup`.

## Helper script (optional)

`${CLAUDE_PLUGIN_ROOT}/scripts/active-leads/check.sh` is a tiny shell helper that lists active users — useful when the user asks "who are the agents?" without running the full workflow. It just shells through `qobrix-api.sh` and prints a compact `{id, name, email}` table.

## Tunable parameters

All hardcoded in this skill text — adjust here if requirements change:

- Inactivity buckets: 7 / 30 / 100 / 300 days
- High-budget Buy threshold: €400,000
- High-budget Rent threshold: €4,000/mo
- Active statuses: `new`, `assigned`, `informative`, `proposal`, `viewing`, `negotiation`

## Notes

- Don't hardcode an agents table — agent rosters change. Always discover via `GET /api/v2/users`.
- Don't use Telegram delivery here — print to chat by default, WhatsApp on request.
- Inactivity is `now - modified`. Don't use `created` — that gives lifetime, not staleness.
