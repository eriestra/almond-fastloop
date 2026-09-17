#!/usr/bin/env python3
"""Build and publish the Browser Use Olympics Hall of Fame from the events collection."""
import json, urllib.request, os, datetime, html, sys
c = json.load(open(os.path.expanduser('~/.almond-private/browser-use-olympics.json')))
def mcp(name, args):
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}
    body = urllib.request.urlopen(urllib.request.Request("https://almond.build/mcp", data=json.dumps(req).encode(), headers={"content-type": "application/json", "accept": "application/json, text/event-stream"}), timeout=60).read().decode()
    line = [l for l in body.splitlines() if l.startswith("data:")]; obj = json.loads(line[-1][5:]) if line else json.loads(body); res = obj.get("result") or {}
    sc = res.get("structuredContent")
    if sc is None:
        try: sc = json.loads(res["content"][0]["text"])
        except Exception: sc = res
    return sc
recs = []; cursor = None
while True:
    r = mcp("record_query", {"siteId": c["siteId"], "writeToken": c["writeToken"], "collection": "events", "limit": 100, **({"cursor": cursor} if cursor else {})})
    recs += r.get("records") or []
    cursor = r.get("nextCursor") if r.get("hasMore") else None
    if not cursor: break
RENAMES = {"fastloop": "Almond-fastloop"}
runs = {}
for r in recs:
    v = r.get("values") or {}
    if isinstance(v, str):
        try: v = json.loads(v)
        except Exception: v = {}
    run = v.get("run")
    if not run: continue
    R = runs.setdefault(run, {"run": run, "team": RENAMES.get(v.get("team") or "unknown", v.get("team") or "unknown"), "model": v.get("model") or "", "harness": v.get("harness") or "", "events": {}, "start": None, "finish": None, "start_at": None, "finish_at": None})
    if v.get("stage") == "start": R["start"] = r.get("createdAt"); R["start_at"] = r.get("createdAt")
    elif v.get("stage") == "finish": R["finish"] = v.get("ms"); R["finish_at"] = r.get("createdAt"); R["tin"] = v.get("tokens_in"); R["tout"] = v.get("tokens_out"); R["tnote"] = v.get("tokens_note") or ""
    elif v.get("stage") == "done": R["events"][v.get("event")] = {"ok": bool(v.get("ok")), "ms": v.get("ms"), "at": r.get("createdAt")}
    R.setdefault("n_start", 0); R.setdefault("n_finish", 0)
    if v.get("stage") == "start": R["n_start"] += 1
    if v.get("stage") == "finish": R["n_finish"] += 1
MIN_EVENT_MS, MIN_TOTAL_MS, CLOCK_SLACK_MS = 300, 3000, 4000
def integrity(R):
    flags = []
    if R.get("n_start", 0) != 1: flags.append("start records != 1")
    if R.get("n_finish", 0) > 1: flags.append("multiple finish records")
    evs = [R["events"].get(k) for k in ["e1", "e2", "e3", "e4", "e5"]]
    if R["finish"] is not None and any(e is None for e in evs): flags.append("missing events")
    prev_ms, prev_at = 0, R["start_at"]
    for k, e in zip(["e1", "e2", "e3", "e4", "e5"], evs):
        if not e: continue
        if e["ms"] is None or e["ms"] < prev_ms: flags.append(f"{k} out of order")
        elif e["ms"] - prev_ms < MIN_EVENT_MS: flags.append(f"{k} under {MIN_EVENT_MS} ms")
        if R["start_at"] and e.get("at") and abs((e["at"] - R["start_at"]) - (e["ms"] or 0)) > CLOCK_SLACK_MS: flags.append(f"{k} client/server clock mismatch")
        prev_ms = e["ms"] or prev_ms
    if R["finish"] is not None and R["finish"] < MIN_TOTAL_MS: flags.append(f"total under {MIN_TOTAL_MS} ms")
    if R["start_at"] and R["finish_at"] and abs((R["finish_at"] - R["start_at"]) - (R["finish"] or 0)) > CLOCK_SLACK_MS: flags.append("finish clock mismatch")
    return flags
rows = []
for R in runs.values():
    ok = sum(1 for e in R["events"].values() if e["ok"]); n = len(R["events"])
    server_total = (R["finish_at"] - R["start_at"]) / 1000 if R["start_at"] and R["finish_at"] else None
    fl = integrity(R)
    rows.append({**R, "ok": ok, "n": n, "server_total": server_total, "complete": R["finish"] is not None, "flags": fl})
rows.sort(key=lambda x: (not x["complete"], bool(x["flags"]), -x["ok"], x["server_total"] or 1e9))
def fmt(x): return "—" if x is None else f"{x:.1f}s"
PRICES = [("jev", 0.042, 0.0), ("gpt-5.6-sol", 5.0, 30.0), ("gpt-5.6-terra", 2.5, 15.0), ("gpt-5.6-luna", 1.0, 6.0), ("gpt-6", 5.0, 30.0), ("claude-fable-5", 10.0, 50.0), ("claude-opus-5", 5.0, 25.0), ("claude-opus", 5.0, 25.0), ("claude-sonnet-5", 2.0, 10.0), ("claude-sonnet", 3.0, 15.0), ("claude-haiku", 1.0, 5.0), ("opus", 5.0, 25.0), ("sonnet", 2.0, 10.0), ("haiku", 1.0, 5.0)]
def cost(R):
    if R.get("tin") is None and R.get("tout") is None: return "—"
    m = (R.get("model") or "").lower(); p = next((p for p in PRICES if p[0] in m), None)
    if not p: return "n/a (model unknown)"
    return f"${((R.get('tin') or 0) * p[1] + (R.get('tout') or 0) * p[2]) / 1e6:,.4f}"
def toks(R):
    if R.get("tin") is None and R.get("tout") is None: return "not reported"
    return f"{R.get('tin') or 0:,} in / {R.get('tout') or 0:,} out" + (f"<br><span class='muted'>{html.escape(R.get('tnote') or '')}</span>" if R.get("tnote") else "")
def evc(R, k): e = R["events"].get(k); return "·" if not e else ("✓" if e["ok"] else "✗")
# one row per team: the fastest finished, unflagged, all-events-passed run; other runs are counted
best = {}; attempts = {}
for R in rows:
    if not R["complete"] or R["flags"]: continue
    key = R["team"].strip().lower(); attempts[key] = attempts.get(key, 0) + 1
    if key not in best or (R["ok"], -(R["server_total"] or 1e9)) > (best[key]["ok"], -(best[key]["server_total"] or 1e9)): best[key] = R
ranked = sorted(best.values(), key=lambda x: (-x["ok"], x["server_total"] or 1e9))
for R in ranked: R["attempts"] = attempts[R["team"].strip().lower()]
trs = "".join(f"<tr><td>{i+1}</td><td><strong>{html.escape(R['team'])}</strong><br><span class='muted'>{html.escape(R['model'])} · {html.escape(R['harness'])}</span></td><td>{R['ok']}/5</td><td>{fmt(R['server_total'])}<br><span class='muted'>best of {R['attempts']}</span></td><td>{toks(R)}</td><td>{cost(R)}</td><td class='muted'>{datetime.datetime.fromtimestamp((R['start_at'] or 0)/1000).strftime('%Y-%m-%d %H:%M') if R['start_at'] else '—'}</td><td class='muted'>{R['run']}</td></tr>" for i, R in enumerate(ranked))
flagged = "".join(f"<li>{html.escape(R['team'])} · run {R['run']} · {R['ok']}/5 · {fmt(R['server_total'])} · {html.escape('; '.join(R['flags']))}</li>" for R in rows if R["complete"] and R["flags"])
dnf = "".join(f"<li>{html.escape(R['team'])} · run {R['run']} · {R['ok']}/{R['n']} events, no finish</li>" for R in rows if not R["complete"])
page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Hall of Fame · Browser Use Olympics by Almond</title>
<style>:root{{--ink:#17130f;--bone:#f5f2ec;--paper:#fbf9f5;--rule:#ddd7cc;--accent:#b5622d}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bone);color:var(--ink);font:16px/1.5 -apple-system,Inter,Helvetica,Arial,sans-serif}}.wrap{{max-width:900px;margin:0 auto;padding:28px 20px 60px}}h1{{font-size:34px;letter-spacing:-.03em;margin:0 0 6px}}.kicker{{font:12px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}}table{{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--rule);border-radius:14px;overflow:hidden}}th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid var(--rule);vertical-align:top}}th{{font:12px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.1em;text-transform:uppercase;color:#6e665d}}.muted{{color:#6e665d;font-size:13px}}a{{color:inherit}}</style></head><body><div class='wrap'>
<div style='display:flex;align-items:center;justify-content:space-between;padding:14px 0;border-bottom:1px solid var(--rule);margin-bottom:18px'><a href='https://almond.build/' style='display:inline-flex;align-items:center;gap:10px;text-decoration:none;font-weight:650;font-size:19px;letter-spacing:-.04em'><svg width='16' height='24' viewBox="-55 -94 110 188" aria-hidden="true"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2f8f6b"/><stop offset="1" stop-color="#7557c7"/></linearGradient></defs><path fill="url(#g)" d="M0-86.6A100 100 0 0 1 0 86.6 100 100 0 0 1 0-86.6Z"/></svg><span>almond</span></a><span style='font:11px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:#6e665d'>Browser Use Olympics</span></div><p class='kicker'>Browser Use Olympics by Almond · Hall of Fame</p><h1>Every run, one clock.</h1>
<p>One row per agent: its fastest finished run that passed the integrity checks, with the number of attempts. Total time is measured by the server, from the Start run record to the Finish run record. Events are scored by the pages themselves. <a href='./'>Take part</a>.</p>
<table><thead><tr><th>#</th><th>Team · model · harness</th><th>Events</th><th>Total</th><th>Tokens (self-reported)</th><th>Cost at list price</th><th>When</th><th>Run</th></tr></thead><tbody>{trs or "<tr><td colspan=8 class='muted'>No finished runs yet.</td></tr>"}</tbody></table>

{('<h2>Flagged, not ranked</h2><p class=muted>Runs whose record chain fails an integrity check or a plausibility floor. They stay visible.</p><ul class=muted>'+flagged+'</ul>') if flagged else ''}
<p class='muted'>Only finished runs that pass the integrity checks are ranked. Checks: one start record, events in order, no event faster than 300 ms, total over 3 s, client and server clocks agree within 4 s. Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} from {len(recs)} event records. Tokens are self-reported by each agent at the finish line; cost is computed from the declared model at public API list prices (uncached input rate), see prices.md in the repository.</p><footer style='margin-top:40px;padding-top:16px;border-top:1px solid var(--rule);font:12px/1.5 ui-monospace,Menlo,monospace;color:#6e665d'>Browser Use Olympics by <a href='https://almond.build/'>Almond</a> · the site, the clock and the Hall of Fame run on Almond · <a href='./'>Take part</a> · <a href='https://github.com/eriestra/almond-fastloop'>source</a></footer>
</div></body></html>"""
out = os.environ.get("HALL_OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "site", "hall.html"); os.makedirs(os.path.dirname(out), exist_ok=True); open(out, "w").write(page)
if "--publish" in sys.argv:
    import hashlib, re as _re
    stable = _re.sub(r"Generated [0-9: -]+", "", page)  # ignore the timestamp when deciding whether anything changed
    digest = hashlib.sha256(stable.encode()).hexdigest(); marker = os.path.expanduser("~/.almond-private/browser-use-olympics-hall.sha")
    last = open(marker).read().strip() if os.path.exists(marker) else ""
    if digest == last and "--force" not in sys.argv: print("hall unchanged; not republished")
    else:
        p = mcp("page_publish", {"siteId": c["siteId"], "writeToken": c["writeToken"], "slug": "hall", "html": page}); print("published hall:", p.get("url") or p.get("error"))
        if p.get("ok"): open(marker, "w").write(digest)
print(f"runs: {len(rows)}  finished: {sum(1 for r in rows if r['complete'])}  records: {len(recs)}")
for R in rows: print(f"  {R['run']} {R['team']:14} {R['ok']}/5 {fmt(R['server_total'])} {'finished' if R['complete'] else 'DNF'}")
