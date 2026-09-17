#!/usr/bin/env python3
"""Compute steps, wall time, per-step latency and tokens from a Codex rollout .jsonl (interactive or exec)."""
import json, sys, glob, os, datetime
def load(path):
    rows = []
    for line in open(path, errors="ignore"):
        try: rows.append(json.loads(line))
        except Exception: pass
    return rows
def ts(r):
    t = r.get("timestamp") or (r.get("payload") or {}).get("timestamp")
    if not t: return None
    try: return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
    except Exception: return None
def main(path):
    rows = load(path)
    times = [ts(r) for r in rows if ts(r)]
    calls = []; tokens_in = 0; tokens_out = 0; last_usage = None
    for r in rows:
        p = r.get("payload") or {}
        s = json.dumps(p)
        if p.get("type") in ("function_call", "custom_tool_call") or '"type": "function_call"' in s or '"type":"function_call"' in s:
            name = p.get("name") or ""
            if "js" in name or "node_repl" in name or "sky" in s: calls.append((ts(r), name))
        if r.get("type") == "token_count" or p.get("type") == "token_count":
            u = (p.get("info") or {}).get("total_token_usage") or p.get("total_token_usage") or {}
            if u: last_usage = u
    if last_usage:
        tokens_in = last_usage.get("input_tokens", 0) + last_usage.get("cached_input_tokens", 0); tokens_out = last_usage.get("output_tokens", 0)
    start, end = (min(times), max(times)) if times else (None, None)
    print(f"rollout: {os.path.basename(path)}")
    print(f"wall: {(end-start).total_seconds():.1f}s" if start else "wall: ?")
    print(f"sky/node_repl tool calls: {len(calls)}")
    for i in range(1, len(calls)):
        if calls[i][0] and calls[i-1][0]: print(f"  step {i}: {(calls[i][0]-calls[i-1][0]).total_seconds():.1f}s between calls")
    print(f"tokens: input+cached={tokens_in} output={tokens_out}")
if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(os.path.expanduser("~/.codex/sessions/*/*/*/*.jsonl")), key=os.path.getmtime)[-1]
    main(path)
