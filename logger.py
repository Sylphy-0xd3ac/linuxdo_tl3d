import json, os, sys
from pathlib import Path
from datetime import datetime, timezone

date_str = os.environ.get("SNAPSHOT_DATE", "")
if not date_str:
    date_str = str(datetime.now(timezone.utc).date())

snapshot_path = Path(f"snapshots/{date_str}.json")
if not snapshot_path.exists():
    print(f"ERROR: {snapshot_path} not found", file=sys.stderr)
    sys.exit(1)

snapshot = json.loads(snapshot_path.read_text())
users = snapshot.get("new_users", [])
count = snapshot.get("count", 0)

summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
if not summary_path:
    print("GITHUB_STEP_SUMMARY not set, printing to stdout")
    summary_path = "/dev/stdout"

lines = []
lines.append(f"date: {date_str}")
lines.append(f"new TL3 users: {count}")
lines.append("")
if users:
    for u in users:
        dt = datetime.fromisoformat(u["granted_at"].replace("Z", "+00:00"))
        lines.append(f"  {u['username']}  {dt.strftime('%H:%M:%S UTC')}")
else:
    lines.append("  no new users today")

with open(summary_path, "a") as f:
    f.write("\n".join(lines) + "\n")
