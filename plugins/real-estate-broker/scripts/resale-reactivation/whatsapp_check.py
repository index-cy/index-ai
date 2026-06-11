#!/usr/bin/env python3
"""
Resale reactivation — daily WhatsApp "still available?" outreach to sellers
whose resale listings have gone stale (inspection_date older than 1 month).

Reads Qobrix + WaSender credentials from the plugin's standard credentials
file. Reads campaign-specific knobs (daily_cap, message template, interval,
cooldown, country code) from a per-tenant campaign.json. State and logs are
kept beside campaign.json so each tenant runs independently.

Credential resolution mirrors scripts/qobrix-api.sh:
  1. CLAUDE_PLUGIN_OPTION_* env vars
  2. Cowork persistent mount: /sessions/*/mnt/.claude/...
  3. Local Claude Code: $HOME/.claude/...

Safe to re-run on crash: state is written BEFORE the send. A "pending"
record blocks resends until the next-day run clears it.

Usage:
  whatsapp_check.py                 # normal run (respects daily cap)
  whatsapp_check.py --dry-run       # list candidates, no sending
  whatsapp_check.py --test <e164>   # send one real message to a given number
        [--test-property <uuid>]
  whatsapp_check.py --status        # print queue + sent counts
  whatsapp_check.py --init-campaign # write a default campaign.json
"""

from __future__ import annotations
import argparse
import datetime as dt
import fcntl
import glob
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

try:
    import certifi  # type: ignore
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CTX = ssl.create_default_context()

PLUGIN_DATA_SUBPATH = "plugins/data/real-estate-broker"
CAMPAIGN_SUBDIR = "resale-reactivation"


def resolve_claude_dir() -> Path:
    """Mirror the bash wrapper's CLAUDE_DIR resolution."""
    for candidate in glob.glob("/sessions/*/mnt/.claude"):
        if os.path.isdir(candidate):
            return Path(candidate)
    return Path(os.path.expanduser("~/.claude"))


CLAUDE_DIR = resolve_claude_dir()
PLUGIN_DATA = CLAUDE_DIR / PLUGIN_DATA_SUBPATH
CAMPAIGN_DIR = PLUGIN_DATA / CAMPAIGN_SUBDIR
CREDS_PATH = PLUGIN_DATA / "credentials.json"
CAMPAIGN_PATH = CAMPAIGN_DIR / "campaign.json"
STATE_PATH = CAMPAIGN_DIR / "state.json"
LOG_PATH = CAMPAIGN_DIR / "run.log"
LOCK_PATH = CAMPAIGN_DIR / ".run.lock"


DEFAULT_CAMPAIGN = {
    "daily_cap": 25,
    "send_interval_seconds": 45,
    "resend_cooldown_days": 120,
    "default_country_code": "+357",
    "message_template": (
        "Hello,\n"
        "I hope you are well. Could you please confirm if your property "
        "({name}{maybe_url}) is still available and advise the current price as of today?\n\n"
        "Thank you in advance."
    ),
    "agency_signature": "",
    "search_dql": (
        "construction_stage in ['resale'] and status in ['available'] "
        "and inspection_date != null and inspection_date < \"{cutoff_date}\""
    ),
    "cutoff_days": 30,
}


def ensure_campaign_dir() -> None:
    CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)


def load_credentials() -> dict:
    """Env vars first, fall back to credentials.json."""
    out = {
        "qobrix_api_url": os.environ.get("CLAUDE_PLUGIN_OPTION_QOBRIX_API_URL", ""),
        "qobrix_api_key": os.environ.get("CLAUDE_PLUGIN_OPTION_QOBRIX_API_KEY", ""),
        "qobrix_api_user": os.environ.get("CLAUDE_PLUGIN_OPTION_QOBRIX_API_USER", ""),
        "wasender_api_key": os.environ.get("CLAUDE_PLUGIN_OPTION_WASENDER_API_KEY", ""),
    }
    if CREDS_PATH.exists():
        try:
            with CREDS_PATH.open() as f:
                file_creds = json.load(f)
            for k in out:
                if not out[k]:
                    out[k] = file_creds.get(k, "")
        except Exception as e:
            sys.stderr.write(f"warning: failed to read {CREDS_PATH}: {e}\n")
    missing = [k for k, v in out.items() if not v]
    if missing:
        raise RuntimeError(
            "credentials missing: " + ", ".join(missing)
            + ". Run /setup in Claude Code to configure them."
        )
    return out


def load_campaign() -> dict:
    if not CAMPAIGN_PATH.exists():
        return dict(DEFAULT_CAMPAIGN)
    with CAMPAIGN_PATH.open() as f:
        user_cfg = json.load(f)
    merged = dict(DEFAULT_CAMPAIGN)
    merged.update(user_cfg)
    return merged


def write_default_campaign() -> Path:
    ensure_campaign_dir()
    if CAMPAIGN_PATH.exists():
        sys.stderr.write(f"campaign.json already exists at {CAMPAIGN_PATH}, leaving untouched.\n")
        return CAMPAIGN_PATH
    with CAMPAIGN_PATH.open("w") as f:
        json.dump(DEFAULT_CAMPAIGN, f, indent=2)
    return CAMPAIGN_PATH


def load_state() -> dict:
    if STATE_PATH.exists():
        with STATE_PATH.open() as f:
            return json.load(f)
    return {"sent": {}, "pending": {}, "runs": []}


def save_state(state: dict) -> None:
    ensure_campaign_dir()
    tmp = STATE_PATH.with_suffix(".json.tmp")
    with tmp.open("w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    tmp.replace(STATE_PATH)


def log(msg: str) -> None:
    ensure_campaign_dir()
    line = f"{dt.datetime.now().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")


def acquire_singleton_lock():
    ensure_campaign_dir()
    fh = open(LOCK_PATH, "w")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.stderr.write(
            f"another whatsapp_check.py run is already in progress (lock: {LOCK_PATH}). exiting.\n"
        )
        sys.exit(0)
    fh.write(str(os.getpid()))
    fh.flush()
    return fh


# ---------------------- HTTP ----------------------

def http_json(method: str, url: str, *, headers: dict, body=None, timeout: int = 30):
    data = None
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Accept": headers.get("Accept", "application/json"),
        **headers,
    }
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw.decode(errors="replace")}


# ---------------------- Qobrix ----------------------

def qobrix_headers(creds: dict) -> dict:
    return {
        "Accept": "application/json",
        "X-Api-Key": creds["qobrix_api_key"],
        "X-Api-User": creds["qobrix_api_user"],
    }


def qobrix_search_properties(creds: dict, campaign: dict) -> list[dict]:
    base = creds["qobrix_api_url"].rstrip("/") + "/api/v2/properties"
    cutoff_days = int(campaign.get("cutoff_days", 30))
    cutoff_date = (dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(days=cutoff_days)).strftime("%Y-%m-%d")
    dql_template = campaign.get("search_dql", DEFAULT_CAMPAIGN["search_dql"])
    dql = dql_template.format(cutoff_date=cutoff_date)
    all_rows: list[dict] = []
    page = 1
    while True:
        qs = urllib.parse.urlencode(
            [
                ("search", dql),
                ("expand", "false"),
                ("media", "false"),
                ("limit", "100"),
                ("page", str(page)),
                ("include[]", "SellerContacts"),
            ]
        )
        status, body = http_json("GET", f"{base}?{qs}", headers=qobrix_headers(creds))
        if status != 200:
            raise RuntimeError(f"qobrix search failed [{status}]: {body}")
        rows = body.get("data", [])
        if not rows:
            break
        all_rows.extend(rows)
        pag = body.get("pagination") or {}
        if not pag.get("has_next_page"):
            break
        page += 1
        if page > 200:
            break
    return all_rows


def qobrix_post_comment(creds: dict, property_id: str, content: str) -> tuple[int, dict]:
    url = creds["qobrix_api_url"].rstrip("/") + f"/api/v2/properties/{property_id}/comments"
    return http_json("POST", url, headers=qobrix_headers(creds), body={"content": content})


# ---------------------- Phone formatting ----------------------

def format_phone(raw: str | None, default_cc: str = "+357") -> str | None:
    if not raw:
        return None
    s = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
    if not s:
        return None
    if s.startswith("+"):
        return s
    if s.startswith("00"):
        return "+" + s[2:]
    if len(s) == 8:
        return default_cc + s
    return default_cc + s


def pick_phone(seller_contact: dict | None, default_cc: str) -> str | None:
    if not seller_contact:
        return None
    for key in ("phone", "phone_2", "phone_3"):
        f = format_phone(seller_contact.get(key), default_cc)
        if f:
            return f
    return None


# ---------------------- WaSender ----------------------

def wasender_send(creds: dict, to: str, text: str) -> tuple[int, dict]:
    url = "https://wasenderapi.com/api/send-message"
    headers = {"Authorization": f"Bearer {creds['wasender_api_key']}"}
    return http_json("POST", url, headers=headers, body={"to": to, "text": text})


def wasender_status(creds: dict) -> tuple[int, dict]:
    return http_json(
        "GET",
        "https://wasenderapi.com/api/status",
        headers={"Authorization": f"Bearer {creds['wasender_api_key']}"},
    )


# ---------------------- Candidate selection ----------------------

def build_candidates(properties: list[dict], state: dict, campaign: dict):
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    cooldown = dt.timedelta(days=int(campaign.get("resend_cooldown_days", 120)))
    default_cc = campaign.get("default_country_code", "+357")

    sent = state.get("sent", {})
    pending = state.get("pending", {})

    seen_sellers = set()
    candidates = []
    skipped_no_phone = 0
    skipped_duplicate_seller = 0
    skipped_cooldown = 0
    skipped_pending = 0

    def sort_key(p):
        return p.get("inspection_date") or ""

    for prop in sorted(properties, key=sort_key):
        pid = prop.get("id")
        seller_id = prop.get("seller")
        if pid in pending:
            skipped_pending += 1
            continue
        last = sent.get(pid)
        if last:
            try:
                last_dt = dt.datetime.fromisoformat(last.replace("Z", ""))
                if now - last_dt < cooldown:
                    skipped_cooldown += 1
                    continue
            except Exception:
                pass
        if seller_id in seen_sellers:
            skipped_duplicate_seller += 1
            continue
        phone = pick_phone(prop.get("seller_contact"), default_cc)
        if not phone:
            skipped_no_phone += 1
            continue
        seller_last = sent.get(f"seller:{seller_id}")
        if seller_last:
            try:
                sd = dt.datetime.fromisoformat(seller_last.replace("Z", ""))
                if now - sd < cooldown:
                    skipped_cooldown += 1
                    continue
            except Exception:
                pass
        seen_sellers.add(seller_id)
        candidates.append({
            "id": pid,
            "seller_id": seller_id,
            "name": prop.get("name") or "",
            "website_url": prop.get("website_url") or "",
            "phone": phone,
            "inspection_date": prop.get("inspection_date"),
        })

    return candidates, {
        "skipped_no_phone": skipped_no_phone,
        "skipped_duplicate_seller": skipped_duplicate_seller,
        "skipped_cooldown": skipped_cooldown,
        "skipped_pending": skipped_pending,
    }


def render_message(template: str, name: str, website_url: str, signature: str = "") -> str:
    maybe_url = f" {website_url}" if website_url else ""
    body = template.format(name=name, maybe_url=maybe_url)
    if signature:
        body = f"{body}\n\n{signature}"
    return body


# ---------------------- Main run ----------------------

def run(creds: dict, campaign: dict, *, dry_run: bool = False) -> dict:
    state = load_state()
    log("fetching properties from Qobrix…")
    properties = qobrix_search_properties(creds, campaign)
    log(f"Qobrix returned {len(properties)} matching properties")

    candidates, stats = build_candidates(properties, state, campaign)
    log(
        f"candidates={len(candidates)} skipped_no_phone={stats['skipped_no_phone']} "
        f"skipped_dup_seller={stats['skipped_duplicate_seller']} "
        f"skipped_cooldown={stats['skipped_cooldown']} "
        f"skipped_pending={stats['skipped_pending']}"
    )

    cap = int(campaign.get("daily_cap", 25))
    interval = int(campaign.get("send_interval_seconds", 45))
    signature = campaign.get("agency_signature", "")
    todo = candidates

    if dry_run:
        log("DRY RUN — first 10 candidates:")
        for c in todo[:10]:
            log(
                f"  {c['id']} seller={c['seller_id']} phone={c['phone']} "
                f"inspect={c['inspection_date']} name={c['name'][:60]!r}"
            )
        return {
            "total_matches": len(properties),
            "candidates": len(candidates),
            "todo": len(candidates),
            **stats,
        }

    s, body = wasender_status(creds)
    if s != 200 or body.get("status") != "connected":
        raise RuntimeError(f"WaSender not connected: status={s} body={body}")

    sent_now = []
    errors = []
    for i, c in enumerate(todo, 1):
        if len(sent_now) >= cap:
            break
        pid = c["id"]
        phone = c["phone"]
        text = render_message(campaign["message_template"], c["name"], c["website_url"], signature)

        state.setdefault("pending", {})[pid] = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat()
        save_state(state)

        log(f"[sent {len(sent_now)+1}/{cap} | attempt {i}] sending to {phone} ({c['name'][:40]})")
        code, resp = wasender_send(creds, phone, text)
        if code not in (200, 201):
            log(f"  ERROR [{code}] {resp}")
            errors.append({"id": pid, "phone": phone, "code": code, "resp": resp})
            state.get("pending", {}).pop(pid, None)
            save_state(state)
            time.sleep(5)
            continue

        now_iso = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat()
        state.setdefault("sent", {})[pid] = now_iso
        state["sent"][f"seller:{c['seller_id']}"] = now_iso
        state.get("pending", {}).pop(pid, None)
        save_state(state)

        ccode, cbody = qobrix_post_comment(creds, pid, f"WA_check_sent_{int(time.time())} to {phone}")
        if ccode not in (200, 201):
            log(f"  (comment post non-fatal fail [{ccode}] {cbody})")

        sent_now.append({"id": pid, "phone": phone})
        if i < len(todo):
            time.sleep(interval)

    state.setdefault("runs", []).append(
        {"ts": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(), "sent": len(sent_now), "errors": len(errors)}
    )
    save_state(state)
    log(f"RUN COMPLETE sent={len(sent_now)} errors={len(errors)}")
    return {
        "sent": len(sent_now),
        "errors": errors,
        "total_matches": len(properties),
        "candidates_total": len(candidates),
    }


def status_summary() -> None:
    state = load_state()
    sent_ids = [k for k in state.get("sent", {}) if not k.startswith("seller:")]
    pending = state.get("pending", {})
    runs = state.get("runs", [])[-5:]
    print(f"campaign_dir            : {CAMPAIGN_DIR}")
    print(f"sent_count_all_time     : {len(sent_ids)}")
    print(f"pending_write_ahead_rows: {len(pending)}")
    print("last_5_runs             :")
    for r in runs:
        print(f"  {r}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--init-campaign", action="store_true",
                    help="Write a default campaign.json and exit")
    ap.add_argument("--test", help="send one real message to this E.164 number and exit")
    ap.add_argument("--test-property", help="optional property UUID for --test payload variables")
    args = ap.parse_args()

    if args.init_campaign:
        path = write_default_campaign()
        print(f"campaign config: {path}")
        return

    creds = load_credentials()
    campaign = load_campaign()

    if args.status:
        status_summary()
        return

    if args.dry_run:
        run(creds, campaign, dry_run=True)
        return

    _lock_fh = acquire_singleton_lock()  # noqa: F841

    if args.test:
        phone = format_phone(args.test, campaign.get("default_country_code", "+357"))
        name = "TEST property"
        url = ""
        if args.test_property:
            base = creds["qobrix_api_url"].rstrip("/") + f"/api/v2/properties/{args.test_property}"
            s, b = http_json("GET", base, headers=qobrix_headers(creds))
            if s == 200 and b.get("data"):
                p = b["data"]
                name = p.get("name") or name
                url = p.get("website_url") or ""
        text = render_message(
            campaign["message_template"], name, url, campaign.get("agency_signature", "")
        )
        log(f"TEST send to {phone}: {text!r}")
        code, resp = wasender_send(creds, phone, text)
        log(f"result: status={code} body={resp}")
        sys.exit(0 if code in (200, 201) else 1)

    run(creds, campaign, dry_run=False)


if __name__ == "__main__":
    main()
