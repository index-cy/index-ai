#!/usr/bin/env bash
# active-leads helper: list active Qobrix users (agents) as a compact table.
#
# Usage:
#   check.sh             # list all active users
#   check.sh <pattern>   # filter by case-insensitive substring on name or email

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PATTERN="${1:-}"

bash "$PLUGIN_ROOT/scripts/qobrix-api.sh" GET "/api/v2/users?limit=100" | \
PATTERN="$PATTERN" python3 -c '
import json, os, sys
pattern = os.environ.get("PATTERN", "").lower()
data = json.load(sys.stdin)
users = data.get("data") if isinstance(data, dict) else []
if not users:
    print(json.dumps(data, indent=2, ensure_ascii=False))
    sys.exit(0)
rows = []
for u in users:
    name = (u.get("name") or f"{u.get(\"first_name\",\"\")} {u.get(\"last_name\",\"\")}").strip()
    email = u.get("email") or ""
    uid = u.get("id") or ""
    if u.get("is_active") is False:
        continue
    if pattern and pattern not in name.lower() and pattern not in email.lower():
        continue
    rows.append((name, email, uid))
rows.sort(key=lambda r: r[0].lower())
w_name = max((len(r[0]) for r in rows), default=4)
w_mail = max((len(r[1]) for r in rows), default=5)
print(f"{\"Name\".ljust(w_name)}  {\"Email\".ljust(w_mail)}  Qobrix ID")
print(f"{\"-\"*w_name}  {\"-\"*w_mail}  {\"-\"*36}")
for n, e, i in rows:
    print(f"{n.ljust(w_name)}  {e.ljust(w_mail)}  {i}")
'
