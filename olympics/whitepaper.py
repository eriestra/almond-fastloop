#!/usr/bin/env python3
"""Render WHITEPAPER.md to the branded Almond page and publish it as /whitepaper."""
import re, html as H, json, urllib.request, os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
md = open(os.path.join(root, 'WHITEPAPER.md')).read().splitlines()
def inline(t):
    t = H.escape(t, quote=False); t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t); t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t); t = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', t)
    return re.sub(r'(?<![">])(https://[^\s<]+)', r'<a href="\1">\1</a>', t)
out = []; i = 0; para = []
def flush():
    global para
    if para: out.append('<p>' + inline(' '.join(para)) + '</p>'); para = []
while i < len(md):
    l = md[i]
    if l.startswith('# '): flush(); out.append('<h1>' + inline(l[2:]) + '</h1>')
    elif l.startswith('## '): flush(); out.append('<h2>' + inline(l[3:]) + '</h2>')
    elif l.startswith('### '): flush(); out.append('<h3>' + inline(l[4:]) + '</h3>')
    elif l.startswith('|'):
        flush(); rows = []
        while i < len(md) and md[i].startswith('|'): rows.append(md[i]); i += 1
        cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows if not re.match(r'^\|[\s\-|:]+\|$', r)]
        out.append('<table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in cells[0]) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in cells[1:]) + '</tbody></table>'); continue
    elif re.match(r'^\s*[-*] ', l):
        flush(); items = []
        while i < len(md) and re.match(r'^\s*[-*] ', md[i]): items.append(re.sub(r'^\s*[-*] ', '', md[i])); i += 1
        out.append('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul>'); continue
    elif re.match(r'^\s*\d+\. ', l):
        flush(); items = []
        while i < len(md) and re.match(r'^\s*\d+\. ', md[i]): items.append(re.sub(r'^\s*\d+\. ', '', md[i])); i += 1
        out.append('<ol>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ol>'); continue
    elif l.strip() == '': flush()
    else: para.append(l.strip())
    i += 1
flush()
body = '\n'.join(out)
css = "<style>:root{--ink:#17130f;--bone:#f5f2ec;--paper:#fbf9f5;--rule:#ddd7cc;--accent:#b5622d}*{box-sizing:border-box}body{margin:0;background:var(--bone);color:var(--ink);font:17px/1.6 -apple-system,Inter,Helvetica,Arial,sans-serif}.wrap{max-width:780px;margin:0 auto;padding:28px 20px 60px}h1{font-size:38px;line-height:1.05;letter-spacing:-.03em;margin:26px 0 8px}h2{font-size:26px;letter-spacing:-.02em;margin:36px 0 10px}h3{font-size:19px;margin:24px 0 8px}p{margin:0 0 14px}table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--rule);border-radius:12px;overflow:hidden;margin:14px 0 20px;font-size:15px}th,td{padding:9px 11px;text-align:left;border-bottom:1px solid var(--rule);vertical-align:top}th{font:12px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.1em;text-transform:uppercase;color:#6e665d}code{background:#eee8de;padding:2px 6px;border-radius:6px;font-size:.92em}a{color:inherit}ul,ol{padding-left:22px}li{margin:6px 0}.brand{display:flex;align-items:center;justify-content:space-between;padding:14px 0;border-bottom:1px solid var(--rule)}.brand a{display:inline-flex;align-items:center;gap:10px;text-decoration:none;font-weight:650;font-size:19px;letter-spacing:-.04em}.brand .tag{font:11px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:#6e665d}footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--rule);font:12px/1.5 ui-monospace,Menlo,monospace;color:#6e665d}</style>"
seed = "<svg width='16' height='24' viewBox='-55 -94 110 188' aria-hidden='true'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#2f8f6b'/><stop offset='1' stop-color='#7557c7'/></linearGradient></defs><path fill='url(#g)' d='M0-86.6A100 100 0 0 1 0 86.6 100 100 0 0 1 0-86.6Z'/></svg>"
page = f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Almond-fastloop and the Browser Use Olympics · whitepaper</title><meta name='description' content='How a bounded-choice decision model makes browser computer use 60 to 80 times faster and thousands of times cheaper, and the benchmark that makes the claim checkable.'>{css}</head><body><div class='wrap'><div class='brand'><a href='https://almond.build/'>{seed}<span>almond</span></a><span class='tag'>Whitepaper</span></div>{body}<footer>Almond-fastloop and the Browser Use Olympics · by <a href='https://almond.build/'>Almond</a> · <a href='./'>Take part</a> · <a href='hall'>Hall of Fame</a> · <a href='https://github.com/eriestra/almond-fastloop'>source and traces</a></footer></div></body></html>"
open(os.path.join(root, 'olympics', 'site', 'whitepaper.html'), 'w').write(page)
if '--publish' in sys.argv:
    c = json.load(open(os.path.expanduser('~/.almond-private/browser-use-olympics.json')))
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "page_publish", "arguments": {"siteId": c["siteId"], "writeToken": c["writeToken"], "slug": "whitepaper", "html": page}}}
    b = urllib.request.urlopen(urllib.request.Request("https://almond.build/mcp", data=json.dumps(req).encode(), headers={"content-type": "application/json", "accept": "application/json, text/event-stream"}), timeout=60).read().decode()
    line = [l for l in b.splitlines() if l.startswith("data:")]; obj = json.loads(line[-1][5:]) if line else json.loads(b); print("published:", ((obj.get("result") or {}).get("structuredContent") or {}).get("url"))
