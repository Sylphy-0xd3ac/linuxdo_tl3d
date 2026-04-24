import subprocess, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

def fetch(offset):
    r = subprocess.run([
        "curl", "-s", "--compressed", "-w", "\n%{http_code}",
        f"https://linux.do/user_badges.json?badge_id=3&offset={offset}",
        "-H", "Accept: application/json",
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.5 Safari/605.1.15",
    ], capture_output=True, text=True)
    *body_lines, status_code = r.stdout.strip().splitlines()
    if status_code == "429":
        print("error: rate limited (429)", file=sys.stderr)
        sys.exit(1)
    if status_code != "200":
        print(f"error: upstream {status_code}", file=sys.stderr)
        sys.exit(1)
    return json.loads("\n".join(body_lines))


from datetime import timedelta

date_override = os.environ.get("FETCH_DATE", "")
if date_override:
    from datetime import date as _date
    today = datetime.combine(_date.fromisoformat(date_override), datetime.min.time()).replace(tzinfo=timezone.utc)
else:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
tomorrow = today + timedelta(days=1)
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
        if today <= granted_at < tomorrow:
            new_users.append({
                "username": user_map.get(b["user_id"], f"uid:{b['user_id']}"),
                "granted_at": b["granted_at"],
                "user_id": b["user_id"],
            })
        elif granted_at < today:
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
