import json,urllib.request,time,datetime,os,sys
c=json.load(open(os.path.expanduser('~/.almond-private/barrio-workshop.json')))
SID,TOK=c['siteId'],c['writeToken']
def mcp(name,args):
    req={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":name,"arguments":args}}
    body=urllib.request.urlopen(urllib.request.Request("https://almond.build/mcp",data=json.dumps(req).encode(),headers={"content-type":"application/json","accept":"application/json, text/event-stream"}),timeout=30).read().decode()
    line=[l for l in body.splitlines() if l.startswith("data:")]; obj=json.loads(line[-1][5:]) if line else json.loads(body); res=obj.get("result") or {}
    sc=res.get("structuredContent")
    if sc is None:
        try: sc=json.loads(res["content"][0]["text"])
        except Exception: sc=res
    return sc
ctx=mcp("site_context",{"siteId":SID,"writeToken":TOK})
cols=ctx.get("collections") or ctx.get("schemas") or []
keys=[(x.get("key") or x.get("collection")) for x in cols] if isinstance(cols,list) else list(cols.keys())
col=sys.argv[1] if len(sys.argv)>1 else (keys[0] if keys else None)
print("collections:",keys,"-> watching:",col,flush=True)
seen=set(); first=True
while True:
    try:
        r=mcp("record_query",{"siteId":SID,"writeToken":TOK,"collection":col,"limit":5})
        recs=r.get("records") or r.get("items") or []
        for rec in recs:
            rid=rec.get("_id") or rec.get("id") or json.dumps(rec)[:60]
            if rid in seen: continue
            seen.add(rid)
            if not first:
                ct=rec.get("createdAt") or rec.get("_creationTime") or 0
                t=datetime.datetime.fromtimestamp(ct/1000) if ct else datetime.datetime.now()
                print(f"NEW RECORD at {t.strftime('%H:%M:%S.%f')[:-3]}  fields={json.dumps(rec.get('fields') or rec.get('data') or rec)[:160]}",flush=True)
        first=False
    except Exception as e: print("err",str(e)[:120],flush=True)
    time.sleep(1)
