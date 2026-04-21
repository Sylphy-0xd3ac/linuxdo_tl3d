import json, os, re, sys
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

all_snapshots = sorted(
    [p.stem for p in Path("snapshots").glob("*.json")],
    reverse=True,
)


def fmt_time(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.strftime("%H:%M UTC")


user_cards = ""
if users:
    for u in users:
        user_cards += f"""        <a class="user-card" href="https://linux.do/u/{u['username']}" target="_blank" rel="noopener">
          <div class="user-info">
            <span class="username">@{u['username']}</span>
            <span class="time">{fmt_time(u['granted_at'])}</span>
          </div>
          <span class="badge-pill">TL3</span>
        </a>\n"""
else:
    user_cards = '        <p class="empty">今日暂无新增活跃用户</p>\n'

sidebar_items = ""
for d in all_snapshots:
    active = ' class="active"' if d == date_str else ""
    sidebar_items += f'      <a href="{d}.html"{active}>{d}</a>\n'

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Linux DO TL3 · {date_str}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #0f1117;
      --surface: #161923;
      --surface2: #1e2231;
      --border: #252b3b;
      --accent: #818cf8;
      --accent-dim: rgba(129,140,248,0.12);
      --text: #dde1ec;
      --muted: #7880a0;
      --tl3: #fbbf24;
      --tl3-dim: rgba(251,191,36,0.1);
      --tl3-border: rgba(251,191,36,0.2);
      --r: 10px;
    }}

    body {{
      font-family: 'Inter', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    /* ── Header ── */
    header {{
      position: sticky; top: 0; z-index: 20;
      background: rgba(15,17,23,0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      height: 52px;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 1.75rem;
    }}

    .logo {{
      display: flex; align-items: center; gap: 0.55rem;
      font-size: 0.9rem; font-weight: 600; letter-spacing: -0.01em;
    }}

    .logo-mark {{
      display: flex; align-items: center;
    }}

    .header-right {{
      font-size: 0.75rem; color: var(--muted);
    }}

    /* ── Layout ── */
    .layout {{
      flex: 1;
      display: flex;
      max-width: 1080px;
      margin: 0 auto;
      width: 100%;
      padding: 2rem 1.5rem;
      gap: 2.5rem;
      align-items: flex-start;
    }}

    /* ── Sidebar ── */
    aside {{
      width: 148px; flex-shrink: 0;
      position: sticky; top: 68px;
    }}

    .sidebar-label {{
      font-size: 0.68rem; font-weight: 600;
      text-transform: uppercase; letter-spacing: 0.1em;
      color: var(--muted); margin-bottom: 0.6rem;
      padding-left: 0.5rem;
    }}

    aside a {{
      display: block;
      padding: 0.35rem 0.5rem;
      font-size: 0.8rem; color: var(--muted);
      text-decoration: none; border-radius: 6px;
      transition: color 0.12s, background 0.12s;
    }}

    aside a:hover {{ color: var(--text); background: var(--surface2); }}

    aside a.active {{
      color: var(--accent);
      background: var(--accent-dim);
      font-weight: 500;
    }}

    /* ── Main ── */
    main {{ flex: 1; min-width: 0; }}

    .page-header {{ margin-bottom: 1.5rem; }}

    .page-title {{
      font-size: 1.6rem; font-weight: 600; letter-spacing: -0.03em;
      display: flex; align-items: center; gap: 0.7rem; flex-wrap: wrap;
    }}

    .count-tag {{
      font-size: 0.8rem; font-weight: 500;
      background: var(--tl3-dim); color: var(--tl3);
      border: 1px solid var(--tl3-border);
      padding: 0.2rem 0.65rem; border-radius: 20px;
    }}

    .page-sub {{
      margin-top: 0.35rem;
      font-size: 0.82rem; color: var(--muted);
    }}

    /* ── Grid ── */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 0.65rem;
    }}

    .user-card {{
      display: flex; align-items: center; gap: 0.75rem;
      padding: 0.75rem 0.9rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--r);
      text-decoration: none; color: var(--text);
      transition: border-color 0.15s, background 0.15s, transform 0.12s;
    }}

    .user-card:hover {{
      border-color: var(--accent);
      background: var(--surface2);
      transform: translateY(-2px);
    }}

    .user-info {{
      flex: 1; min-width: 0;
      display: flex; flex-direction: column; gap: 0.18rem;
    }}

    .username {{
      font-size: 0.875rem; font-weight: 500;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}

    .time {{ font-size: 0.72rem; color: var(--muted); }}

    .badge-pill {{
      font-size: 0.68rem; font-weight: 600;
      background: var(--tl3-dim); color: var(--tl3);
      border: 1px solid var(--tl3-border);
      padding: 0.12rem 0.4rem; border-radius: 4px;
      flex-shrink: 0;
    }}

    .empty {{
      color: var(--muted); font-size: 0.875rem; padding: 3rem 0;
    }}

    /* ── Footer ── */
    footer {{
      border-top: 1px solid var(--border);
      padding: 1.25rem 1.75rem;
      text-align: center;
      font-size: 0.72rem; color: var(--muted);
    }}

    footer a {{ color: var(--muted); text-decoration: underline; text-underline-offset: 2px; }}

    /* ── Responsive ── */
    @media (max-width: 600px) {{
      aside {{ display: none; }}
      .layout {{ padding: 1.25rem 1rem; gap: 0; }}
      .grid {{ grid-template-columns: 1fr 1fr; gap: 0.5rem; }}
      .badge-pill {{ display: none; }}
    }}
  </style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-mark"><svg width="22" height="22" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><clipPath id="ld"><circle cx="60" cy="60" r="47"></circle></clipPath><circle fill="#f0f0f0" cx="60" cy="60" r="50"></circle><rect fill="#1c1c1e" clip-path="url(#ld)" x="10" y="10" width="100" height="30"></rect><rect fill="#f0f0f0" clip-path="url(#ld)" x="10" y="40" width="100" height="40"></rect><rect fill="#ffb003" clip-path="url(#ld)" x="10" y="80" width="100" height="30"></rect></svg></div>
    Linux DO · TL3 Tracker
  </div>
  <span class="header-right">Trust Level 3 · 活跃用户</span>
</header>

<div class="layout">
  <aside>
    <div class="sidebar-label">History</div>
{sidebar_items}  </aside>

  <main>
    <div class="page-header">
      <div class="page-title">
        {date_str}
        <span class="count-tag">+{count} 人</span>
      </div>
      <div class="page-sub">当日新晋 Trust Level 3 活跃用户</div>
    </div>

    <div class="grid">
{user_cards}    </div>
  </main>
</div>

<footer>
  数据来自 <a href="https://linux.do" target="_blank">linux.do</a> · badge_id=3 授予事件 · 每日 UTC 21:30 更新
</footer>

</body>
</html>"""

out_path = Path(f"snapshots/{date_str}.html")
out_path.write_text(html, encoding="utf-8")
print(f"rendered {out_path}")

index = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=snapshots/{date_str}.html">
  <title>Linux DO TL3 Tracker</title>
</head>
<body>
  <script>location.replace("snapshots/{date_str}.html")</script>
</body>
</html>"""

Path("index.html").write_text(index, encoding="utf-8")
print(f"updated index.html -> snapshots/{date_str}.html")

# Update aside in all existing HTML snapshots
for html_path in sorted(Path("snapshots").glob("*.html")):
    d = html_path.stem
    if d == date_str:
        continue  # already written above
    new_sidebar = ""
    for s in all_snapshots:
        active = ' class="active"' if s == d else ""
        new_sidebar += f'      <a href="{s}.html"{active}>{s}</a>\n'
    content = html_path.read_text(encoding="utf-8")
    updated = re.sub(
        r'(<aside>\s*<div class="sidebar-label">.*?</div>\s*).*?(</aside>)',
        lambda m: m.group(1) + new_sidebar + "  " + m.group(2),
        content,
        flags=re.DOTALL,
    )
    if updated != content:
        html_path.write_text(updated, encoding="utf-8")
        print(f"updated aside in {html_path.name}")
    else:
        print(f"aside unchanged in {html_path.name}")
