---
name: resale-reactivation
description: >
  Run a daily WhatsApp "still available?" outreach to sellers of stale resale
  listings in Qobrix CRM. Use when the user says "resale reactivation", "asleep
  resale check", "send WhatsApp to stale resale sellers", "ping cold listings",
  "daily resale check", "обзвон вторички", "проверка вторички", or wants to
  reach out to property owners whose listings haven't been refreshed recently.
  Also use when asked to schedule, run, or audit this campaign.
version: 1.0.0
---

# Resale Reactivation Campaign

Iterates Qobrix `construction_stage in ['resale'] and status in ['available']`
properties whose `inspection_date` is older than 1 month, dedupes by seller,
respects a configurable cooldown (default 120 days), and sends up to a daily
cap (default 25) of paced WhatsApp messages asking the seller whether the
property is still available.

Every successful send is recorded both in **local state** (`state.json`) and as
a **comment on the property** in Qobrix (`WA_check_sent_<unix>` — searchable
later via `content contains "WA_check_sent_"`).

## How to invoke

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/resale-reactivation/whatsapp_check.py" [flags]
```

Flags:

| Flag | Effect |
|------|--------|
| (none) | Normal run — sends up to `daily_cap` messages |
| `--dry-run` | Print the first 10 candidates and stop. No messages sent. |
| `--status` | Print campaign location, all-time send count, pending rows, last 5 runs |
| `--test <e164>` | Send ONE real message to the given number and exit. Optional `--test-property <uuid>` lets it pull realistic `name`/`url` from a real property. |
| `--init-campaign` | Write a default `campaign.json` so the user can edit it. Safe — won't overwrite. |

If the script prints `credentials missing` (Qobrix or WaSender keys), tell the
user to run `/setup` to configure them.

## First-time setup

1. Run `--init-campaign`:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/resale-reactivation/whatsapp_check.py" --init-campaign
   ```
   This writes a default `campaign.json` to
   `$CLAUDE_DIR/plugins/data/real-estate-broker/resale-reactivation/`.

2. Review and edit the message template, daily cap, interval, and signature.
   See **Campaign config** below.

3. Verify connectivity:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" GET "/api/status"
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/users?limit=1"
   ```
   Both must succeed before the campaign will run.

4. Do a **dry run** to confirm the candidate query returns sensible properties:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/resale-reactivation/whatsapp_check.py" --dry-run
   ```

5. Optional — send a **single test message** to your own phone:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/resale-reactivation/whatsapp_check.py" \
     --test "+35799999999" --test-property "<some-property-uuid>"
   ```

## Campaign config

Path: `$CLAUDE_DIR/plugins/data/real-estate-broker/resale-reactivation/campaign.json`

Default contents (created by `--init-campaign`):

```json
{
  "daily_cap": 25,
  "send_interval_seconds": 45,
  "resend_cooldown_days": 120,
  "default_country_code": "+357",
  "message_template": "Hello,\nI hope you are well. Could you please confirm if your property ({name}{maybe_url}) is still available and advise the current price as of today?\n\nThank you in advance.",
  "agency_signature": "",
  "search_dql": "construction_stage in ['resale'] and status in ['available'] and inspection_date != null and inspection_date < \"{cutoff_date}\"",
  "cutoff_days": 30
}
```

| Key | Meaning |
|-----|---------|
| `daily_cap` | Maximum messages per run. Started at 30; we dropped to 25 after a WaSender block in production. Don't go above 30 without warming up. |
| `send_interval_seconds` | Sleep between sends. 45s is a safe Cyprus number; lower at your risk. |
| `resend_cooldown_days` | Once a seller (or property) is messaged, suppress for this many days. 120 = roughly one outreach cycle per quarter. |
| `default_country_code` | Prepended when the seller's phone is a bare 8-digit local number. Cyprus = `+357`. |
| `message_template` | Body. Supports `{name}` (property name) and `{maybe_url}` (` <url>` if a `website_url` exists, else empty). Use real `\n` newlines. |
| `agency_signature` | Optional trailing block appended after a blank line. Use for "MySpace real estate / www.example.com" etc. Keep empty if the message template already has a signature. |
| `search_dql` | The Qobrix DQL query. `{cutoff_date}` is substituted with `today - cutoff_days`. Don't edit unless you know what you're doing. |
| `cutoff_days` | "Older than" threshold for `inspection_date`. Default 30. |

## What the script does, step by step

1. **Acquire singleton lock** at `.run.lock` — refuses to start if another run
   is in progress. This is critical: a duplicate run would send each seller a
   second message.
2. **Pre-flight WaSender** with `GET /api/status` — aborts if not `connected`.
3. **Paginate Qobrix** properties matching the DQL above, including
   `SellerContacts`. Sorted by `inspection_date` ascending so the oldest get
   pinged first.
4. **Build candidates** — for each property:
   - Skip if it has a `pending` row (means a prior run crashed mid-send;
     human review needed).
   - Skip if `sent[property_id]` was within `resend_cooldown_days`.
   - Skip if `sent[seller:<seller_id>]` was within cooldown (cross-property
     dedupe — one ping per seller per cycle).
   - Skip if the seller was already chosen earlier in this run (in-memory
     dedupe).
   - Skip if no phone number can be derived from `phone`, `phone_2`,
     `phone_3` on the seller contact.
5. **Send loop** — for each candidate up to `daily_cap`:
   - **Write-ahead**: insert `pending[property_id] = now` and `save_state`.
     This guarantees that even if the script is killed *during* the WaSender
     POST, the next run won't double-send.
   - **POST** `/api/send-message` to WaSender.
   - On success: move from `pending` to `sent`, also stamp `seller:<id>`,
     then post a `WA_check_sent_<unix> to <phone>` comment to the property
     via `/api/v2/properties/<id>/comments`. The comment post is non-fatal —
     send is what counts.
   - On failure: clear `pending`, log the error, back off 5s, continue.
   - Sleep `send_interval_seconds` between sends.
6. **Append run summary** to `state.runs[]` and exit.

## Scheduling (cron)

The original VidiGroup deployment runs this on weekdays at 9:30 AM local time.
Example crontab (Mac/Linux):

```cron
30 9 * * 1-5 /usr/bin/python3 "$HOME/.claude/plugins/cache/index-ai/real-estate-broker/<hash>/scripts/resale-reactivation/whatsapp_check.py" >> "$HOME/.claude/plugins/data/real-estate-broker/resale-reactivation/cron.log" 2>&1
```

Note: `${CLAUDE_PLUGIN_ROOT}` is only set when the script is invoked by Claude.
For cron use, hard-code the absolute path to the installed plugin script (find
it under `~/.claude/plugins/cache/index-ai/real-estate-broker/<hash>/`).

On macOS, launchd is more reliable than cron (cron is deprecated). Offer to
write a `~/Library/LaunchAgents/com.indexai.resale-reactivation.plist` if the
user asks.

## How to answer common user questions

### "How many were sent today?" / "What's the status?"

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/resale-reactivation/whatsapp_check.py" --status
```

Returns campaign dir, all-time sent count, pending count, last 5 runs.

### "Which properties have I pinged?"

The script logs to `run.log` in the campaign dir. Also each ping creates a
Qobrix comment — find all such comments by listing recent properties and
checking their comments sub-resource:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET \
  "/api/v2/properties/<id>/comments?search=content%20contains%20%22WA_check_sent_%22&limit=5"
```

There's no top-level `/comments` endpoint in Qobrix, so a full audit requires
iterating properties (or checking `state.json` locally — that's the cheap path).

### "We got blocked!" / "Slow it down"

Edit `campaign.json`:
- Drop `daily_cap` (start from 25 and go lower)
- Raise `send_interval_seconds` (60+ for cold accounts)
- Verify WaSender session is healthy via `/api/status`

### "Reset the state — start over"

Don't. The cooldown exists to protect sellers from spam. If the user insists,
back up `state.json` first, then delete it:

```bash
cp "$CLAUDE_DIR/plugins/data/real-estate-broker/resale-reactivation/state.json" \
   "$CLAUDE_DIR/plugins/data/real-estate-broker/resale-reactivation/state.bak.$(date +%Y%m%d).json"
rm "$CLAUDE_DIR/plugins/data/real-estate-broker/resale-reactivation/state.json"
```

(`$CLAUDE_DIR` is `/sessions/*/mnt/.claude` in Cowork or `$HOME/.claude` in
Claude Code — same resolution as `qobrix-api.sh`.)

### "Add a test send for myself"

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/resale-reactivation/whatsapp_check.py" \
  --test "+35799779952" --test-property "<some-uuid>"
```

This bypasses the daily cap and dedupe state — it's an outbound test, not part
of the campaign accounting.

## Important notes

- **Singleton lock is non-negotiable.** Two concurrent runs would double-send.
- **Pending rows are sticky on purpose.** If you see `skipped_pending` > 0,
  inspect those property IDs in `state.json` and decide whether they were
  actually delivered (check the recipient's chat or the WaSender dashboard)
  before clearing the pending entry.
- **WaSender requires a `Mozilla/...` UA.** Cloudflare blocks the default
  Python UA. The script already spoofs Safari — don't remove that.
- **DQL gotcha:** `=` is not valid in Qobrix DQL. Always use `in [...]` for
  equality (the script does this already).
- **Phone format:** WaSender accepts E.164 with or without `+`. The script
  emits `+357XXXXXXXX` — both forms work.
- **Property comment is audit, not source of truth.** The cooldown is enforced
  off `state.json`. If you wipe state, the script will happily re-message
  everyone the next morning.
