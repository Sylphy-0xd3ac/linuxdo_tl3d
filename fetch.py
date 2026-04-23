import subprocess, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

TOKEN = os.environ.get("SESSION_TOKEN", "")
WORKER_URL = os.environ.get("WORKER_URL", "")

if not TOKEN:
    print("error: SESSION_TOKEN not set", file=sys.stderr)
    sys.exit(1)
if not WORKER_URL:
    print("error: WORKER_URL not set", file=sys.stderr)
    sys.exit(1)


def fetch(offset):
    r = subprocess.run([
        "curl", "-s", "-w", "\n%{http_code}",
        f"{WORKER_URL}?offset={offset}",
        "-H", "Accept: application/json",
        "-H", f"Cookie: auth.session-token={TOKEN}",
    ], capture_output=True, text=True)
    *body_lines, status_code = r.stdout.strip().splitlines()
    if status_code == "429":
        print("error: rate limited (429)", file=sys.stderr)
        sys.exit(1)
    if status_code != "200":
        print(f"error: upstream {status_code}", file=sys.stderr)
        sys.exit(1)
    return json.loads("\n".join(body_lines))


date_override = os.environ.get("FETCH_DATE", "")
if date_override:
    from datetime import date as _date
    today = datetime.combine(_date.fromisoformat(date_override), datetime.min.time()).replace(tzinfo=timezone.utc)
else:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
date_str = str(today.date())
new_users, offset = [], 0

print(f"fetching badge_id=3 granted on {date_str} UTC")

while True:
    data = fetch(offset)
    user_map = {u["id"]: u["username"] for u in data.get("users", [])}
    badges = data.get("user_badge_info", {}).get("user_badges", [])
    if not badges:
        break
    stop = False
    for b in badges:
        granted_at = datetime.fromisoformat(b["granted_at"].replace("Z", "+00:00"))
        if granted_at >= today:
            new_users.append({
                "username": user_map.get(b["user_id"], f"uid:{b['user_id']}"),
                "granted_at": b["granted_at"],
                "user_id": b["user_id"],
            })
        else:
            stop = True
            break
    if stop:
        break
    offset += len(badges)
    print(f"  fetched offset={offset}, {len(new_users)} new users so far")

print(f"done: {len(new_users)} new TL3 users on {date_str}")

Path("snapshots").mkdir(exist_ok=True)
out_path = Path(f"snapshots/{date_str}.json")
out_path.write_text(json.dumps({
    "date": date_str,
    "count": len(new_users),
    "new_users": new_users,
}, ensure_ascii=False, indent=2))
print(f"wrote {out_path}")

# Pass date downstream
github_output = os.environ.get("GITHUB_OUTPUT", "")
if github_output:
    with open(github_output, "a") as f:
        f.write(f"date={date_str}\n")
        f.write(f"count={len(new_users)}\n")
