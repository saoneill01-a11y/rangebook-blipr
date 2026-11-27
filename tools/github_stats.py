#!/usr/bin/env python3
"""Saves GitHub's visitor numbers for BLIPR and Range Book every day, because GitHub itself only keeps the last 14 days.

Uses the GitHub command-line tool (gh), already signed in, so no token is stored here. Each run:
  - for each repo (its own subfolder), merges the last 14 days of views and clones into daily.csv (one row per day; re-running is harmless),
  - adds today's stars and forks, and the top referring sites and pages so far,
  - rebuilds stats.html, one page with both repos' charts and tables (open it in any browser).
Run daily by launchd (~/Library/LaunchAgents/org.rangebook.github-stats.plist).

    python3 tools/github_stats.py [output folder]
"""
import csv, datetime as dt, html, json, os, subprocess, sys

REPOS = (("BLIPR", "saoneill01-a11y/rangebook-blipr"), ("Range Book", "saoneill01-a11y/rangebook"))
GH = "/opt/homebrew/bin/gh"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/Claude/Range Book Project Files/GitHub stats")
DAILY = ("date", "views", "visitors", "clones", "cloners", "stars", "forks")


def api(repo, path):
    r = subprocess.run([GH, "api", f"repos/{repo}{path}"], capture_output=True, text=True, timeout=60)
    if r.returncode:
        raise SystemExit(f"gh api {path} failed: {r.stderr.strip()}")
    return json.loads(r.stdout)


def load(path, key):
    if not os.path.exists(path):
        return {}
    with open(path, newline="") as f:
        return {key(r): r for r in csv.DictReader(f)}


def save(path, fields, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    os.replace(tmp, path)


def main():
    today = dt.date.today().isoformat()
    sections = [collect(name, repo, today) for name, repo in REPOS]
    write_page(sections, today)


def collect(name, repo, today):
    out = os.path.join(OUT, name)
    os.makedirs(out, exist_ok=True)
    api_ = lambda path: api(repo, path)
    views, clones, info = api_("/traffic/views"), api_("/traffic/clones"), api_("")
    refs, paths = api_("/traffic/popular/referrers"), api_("/traffic/popular/paths")

    dpath = os.path.join(out, "daily.csv")
    days = load(dpath, lambda r: r["date"])
    def row(d):
        return days.setdefault(d, {k: "" for k in DAILY} | {"date": d})
    for v in views.get("views", []):
        r = row(v["timestamp"][:10]); r["views"], r["visitors"] = v["count"], v["uniques"]
    for c in clones.get("clones", []):
        r = row(c["timestamp"][:10]); r["clones"], r["cloners"] = c["count"], c["uniques"]
    r = row(today); r["stars"], r["forks"] = info["stargazers_count"], info["forks_count"]
    save(dpath, DAILY, [days[d] for d in sorted(days)])

    # referrers and pages: GitHub only gives 14-day totals, so keep one snapshot per day
    for fname, items, label in (("referrers.csv", refs, "referrer"), ("pages.csv", paths, "path")):
        p = os.path.join(out, fname)
        old = [r for r in load(p, lambda r: (r["snapshot"], r[label])).values() if r["snapshot"] != today]
        new = [{"snapshot": today, label: i[label], "views": i["count"], "visitors": i["uniques"]} for i in items]
        save(p, ("snapshot", label, "views", "visitors"), old + new)

    print(f"saved {today} {name}: {sum(v['count'] for v in views.get('views', []))} views in the last 14 days -> {out}")
    return section(name, repo, sorted(days.values(), key=lambda r: r["date"]), refs, paths, info)


def section(name, repo, rows, refs, paths, info):
    num = lambda x: int(x) if str(x).strip() else 0
    rows = rows[-120:]
    vmax = max([num(r["views"]) for r in rows] + [1])
    bw = min(40, 900 / max(1, len(rows)))
    W, H = 940, 220
    bars = []
    for i, r in enumerate(rows):
        v, u = num(r["views"]), num(r["visitors"])
        x = 30 + i * bw
        hv, hu = 180 * v / vmax, 180 * u / vmax
        bars.append(f'<rect x="{x:.1f}" y="{195 - hv:.1f}" width="{bw - 2:.1f}" height="{hv:.1f}" fill="var(--a)">'
                    f'<title>{r["date"]}: {v} views, {u} people</title></rect>'
                    f'<rect x="{x:.1f}" y="{195 - hu:.1f}" width="{bw - 2:.1f}" height="{hu:.1f}" fill="var(--b)"/>')
    ticks = "".join(f'<text x="{30 + i * bw:.1f}" y="214" class="t">{r["date"][5:]}</text>'
                    for i, r in enumerate(rows) if i % max(1, len(rows) // 7) == 0)
    total_v = sum(num(r["views"]) for r in rows); total_u = sum(num(r["visitors"]) for r in rows)
    last = rows[-1] if rows else {}
    def table(items, label):
        if not items:
            return "<p class=m>None yet.</p>"
        return "<table><tr><th>" + label + "</th><th>Views</th><th>People</th></tr>" + "".join(
            f"<tr><td>{html.escape(i[label.lower() if label != 'Page' else 'path'])}</td><td>{i['count']}</td>"
            f"<td>{i['uniques']}</td></tr>" for i in items) + "</table>"
    recent = "".join(f"<tr><td>{r['date']}</td><td>{num(r['views'])}</td><td>{num(r['visitors'])}</td>"
                     f"<td>{num(r['clones'])}</td></tr>" for r in reversed(rows[-14:]))
    return f"""<h2>{name}</h2><p class=m><a href="https://github.com/{repo}">{repo}</a> · full history in the
"{name}" folder: daily.csv, referrers.csv, pages.csv (open in Numbers or Excel).</p>
<div class=k><div><b>{total_v}</b>views (all saved days)</div><div><b>{total_u}</b>visitors, added up by day</div>
<div><b>{info['stargazers_count']}</b>stars</div><div><b>{info['forks_count']}</b>forks</div>
<div><b>{num(last.get('views', 0))}</b>views on {last.get('date', '-')}</div></div>
<h3>Views per day <span class=m>(full bar: views, inner bar: different people)</span></h3>
<svg viewBox="0 0 {W} {H}">{''.join(bars)}{ticks}</svg>
<div class=cols><div><h3>Last 14 days</h3><table><tr><th>Day</th><th>Views</th><th>People</th><th>Clones</th></tr>{recent}</table></div>
<div><h3>Where visitors came from <span class=m>(14 days)</span></h3>{table(refs, 'Referrer')}
<h3>Most viewed pages <span class=m>(14 days)</span></h3>{table(paths[:10], 'Page')}</div></div>
<hr>"""


def write_page(sections, today):
    doc = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>GitHub stats</title>
<style>:root{{--bg:#fff;--fg:#1b1d21;--m:#666;--a:#b9dfe2;--b:#2a9aa3;--l:#ddd}}
@media (prefers-color-scheme:dark){{:root{{--bg:#121418;--fg:#e8e8e8;--m:#999;--a:#24494c;--b:#5fc6cd;--l:#333}}}}
body{{background:var(--bg);color:var(--fg);font:15px -apple-system,system-ui,sans-serif;max-width:980px;margin:0 auto;padding:20px 16px}}
h1,h2{{margin:0 0 4px}} h2{{margin-top:24px}} hr{{border:0;border-top:1px solid var(--l);margin:24px 0}} a{{color:var(--b)}} .m{{color:var(--m)}} .k{{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}}
.k div{{border:1px solid var(--l);border-radius:10px;padding:10px 16px}} .k b{{display:block;font-size:26px}}
svg{{width:100%;height:auto}} .t{{font-size:10px;fill:var(--m)}} table{{border-collapse:collapse;margin:6px 0 18px}}
td,th{{text-align:left;padding:4px 14px 4px 0;border-bottom:1px solid var(--l)}} td+td,th+th{{text-align:right}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:0 30px}}</style>
<h1>GitHub stats</h1><p class=m>Updated {today}. GitHub's numbers can run up to a day behind.</p>
{"".join(sections)}"""
    with open(os.path.join(OUT, "stats.html"), "w") as f:
        f.write(doc)


if __name__ == "__main__":
    main()
