// Almond-fastloop — browser computer-use loop: Chrome DevTools state -> TypeSafe choice -> executor.
// No dependencies. Node >= 22 (global fetch + WebSocket).
import { readFileSync } from "node:fs";

const PORT = process.env.FL_PORT || 9333;
const KEY = Object.fromEntries(readFileSync(`${process.env.HOME}/.config/typesafe/env`, "utf8").split("\n").filter(l => l.includes("=")).map(l => l.split("=", 2).map(s => s.trim()))).TYPESAFE_API_KEY;
const MAX_STEPS = Number(process.env.FL_MAX_STEPS || 14);
const MIN_CONF = Number(process.env.FL_MIN_CONF || 0.3);

// ---------- CDP ----------
export class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.events = []; ws.onmessage = (m) => { const o = JSON.parse(m.data); if (o.id && this.pending.has(o.id)) { const { res, rej } = this.pending.get(o.id); this.pending.delete(o.id); o.error ? rej(new Error(o.error.message)) : res(o.result); } else if (o.method) this.events.push(o); }; }
  send(method, params = {}) { const id = ++this.id; return new Promise((res, rej) => { this.pending.set(id, { res, rej }); this.ws.send(JSON.stringify({ id, method, params })); }); }
  async eval(expr) { const r = await this.send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) throw new Error(r.exceptionDetails.text + " " + JSON.stringify(r.exceptionDetails.exception?.description || "").slice(0, 200)); return r.result.value; }
}
export async function connect(urlMatch) {
  let targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  let page = targets.find(t => t.type === "page" && (!urlMatch || t.url.includes(urlMatch))) || targets.find(t => t.type === "page");
  if (!page) { page = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: "PUT" })).json(); }
  if (!page) throw new Error("no page target");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  const cdp = new CDP(ws);
  await cdp.send("Page.enable"); await cdp.send("Runtime.enable");
  return cdp;
}

// ---------- state builder (runs inside the page) ----------
export const STATE_JS = `(() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const inView = r => r.top < innerHeight && r.bottom > 0;
  const nm = el => (el.getAttribute('aria-label') || el.getAttribute('placeholder') || (el.labels && el.labels[0] && el.labels[0].innerText) || (el.tagName === 'SELECT' ? '' : el.innerText) || el.getAttribute('title') || el.getAttribute('alt') || el.name || '').trim().replace(/\\s+/g, ' ').slice(0, 70);
  const sel = 'a[href],button,input:not([type=hidden]),select,textarea,[role=button],[role=link],[role=tab],[role=menuitem],[contenteditable=true],summary';
  const dialogs = [...document.querySelectorAll('dialog[open]')];
  const root = dialogs.length ? dialogs[dialogs.length - 1] : document;
  document.querySelectorAll('[data-fl]').forEach(e => e.removeAttribute('data-fl'));
  let i = 0; const els = [];
  for (const el of root.querySelectorAll(sel)) {
    if (!vis(el)) continue; const r = el.getBoundingClientRect(); const id = ++i; el.setAttribute('data-fl', id);
    const tag = el.tagName.toLowerCase(); const type = (el.type || '').toLowerCase();
    const role = el.getAttribute('role') || (tag === 'a' ? 'link' : tag === 'button' ? (type === 'submit' ? 'submit' : 'button') : tag === 'select' ? 'select' : tag === 'textarea' ? 'textarea' : tag === 'input' ? (type || 'text') : tag);
    const it = { id, role, name: nm(el), inViewport: inView(r) };
    if (tag === 'select') { it.options = [...el.options].map(o => o.text.trim()).slice(0, 12); it.selected = el.options[el.selectedIndex] ? el.options[el.selectedIndex].text.trim() : ''; }
    if (tag === 'input' || tag === 'textarea') { it.value = (el.value || '').slice(0, 40); if (el.required) it.required = true; }
    if (el.disabled) it.disabled = true; if (el === document.activeElement) it.focused = true;
    els.push(it);
  }
  const pageValues = [...new Set([...document.querySelectorAll('code')].filter(vis).map(c => c.innerText.trim()).filter(t => t && t.length <= 60))].slice(0, 8);
  const heads = [...document.querySelectorAll('h1,h2,h3')].filter(vis).slice(0, 8).map(h => h.innerText.trim().replace(/\\s+/g, ' ').slice(0, 80));
  const status = [...document.querySelectorAll('[role=status],[aria-live],output')].map(e => e.innerText.trim()).filter(Boolean).slice(0, 4);
  const text = (root === document ? document.body : root).innerText.replace(/\\s+/g, ' ').slice(0, 700);
  return { url: location.href, title: document.title, ready: document.readyState, scrollY: Math.round(scrollY), pageHeight: document.body.scrollHeight, viewportHeight: innerHeight, dialogOpen: dialogs.length > 0, headings: heads, status, pageValues, elements: els, textSample: text };
})()`;

export function sig(s) { return JSON.stringify([s.url, s.dialogOpen, s.status, s.elements.map(e => [e.role, e.name, e.value, e.selected])]); }
export function diff(prev, cur) {
  if (!prev) return "first observation";
  const out = [];
  if (prev.url !== cur.url) out.push(`navigated to ${cur.url}`);
  if (prev.dialogOpen !== cur.dialogOpen) out.push(cur.dialogOpen ? "a dialog opened" : "the dialog closed");
  const key = e => e.role + "|" + e.name; const p = new Set(prev.elements.map(key)); const c = new Set(cur.elements.map(key));
  const added = cur.elements.filter(e => !p.has(key(e))).slice(0, 6).map(e => `${e.role} '${e.name}'`); const removed = prev.elements.filter(e => !c.has(key(e))).slice(0, 6).map(e => `${e.role} '${e.name}'`);
  if (added.length) out.push("appeared: " + added.join(", ")); if (removed.length) out.push("disappeared: " + removed.join(", "));
  for (const e of cur.elements) { const q = prev.elements.find(x => key(x) === key(e)); if (q && (q.value !== e.value || q.selected !== e.selected)) out.push(`'${e.name}' is now '${e.value ?? e.selected}'`); }
  if (JSON.stringify(prev.status) !== JSON.stringify(cur.status) && cur.status.length) out.push("status: " + cur.status.join(" | "));
  if (Math.abs(prev.scrollY - cur.scrollY) > 40) out.push(`scrolled to ${cur.scrollY}`);
  return out.length ? out.join("; ") : "nothing visible changed";
}

// ---------- options ----------
export function buildOptions(state, task) {
  const opts = {}; const acts = {};
  const seen = Object.fromEntries((task._seen || []).map((v, i) => [`seen_${i}`, v]));
  const shown = Object.fromEntries((state.pageValues || []).map((v, i) => [`shown_${i}`, v]));
  const add = (k, label, act) => { if (Object.keys(opts).length >= 200) return; opts[k] = label; acts[k] = act; };
  for (const e of state.elements) {
    if (e.disabled) continue;
    const where = e.inViewport ? "" : " (below the fold)";
    if (["button", "submit", "link", "tab", "menuitem", "summary", "checkbox", "radio"].includes(e.role)) add(`click_${e.id}`, `Click the ${e.role} '${e.name || "unnamed"}'${where}`, { type: "click", id: e.id });
    else if (e.role === "select") { for (let i = 0; i < (e.options || []).length; i++) { const o = e.options[i]; if (!o || /^(selecciona|select|choose|elige)/i.test(o) || o === e.selected) continue; add(`select_${e.id}_${i}`, `Choose '${o}' in the dropdown '${e.name || "unnamed"}'${where}`, { type: "select", id: e.id, index: i }); } }
    else if (["text", "email", "tel", "search", "url", "number", "textarea", "password"].includes(e.role)) { for (const [k, v] of Object.entries({ ...(task.data || {}), ...seen, ...shown })) { if (e.value && String(v).startsWith(e.value)) continue; if (task._tried && task._tried[`fill_${e.id}_${k}`] >= 2) continue; const label = k.startsWith('seen_') ? `the value '${v}' seen on an earlier page` : k.startsWith('shown_') ? `the value '${v}' that this page shows` : `the ${k} ('${String(v).slice(0, 30)}')`; add(`fill_${e.id}_${k}`, `Type ${label} into the ${e.role} field '${e.name || "unnamed"}'${e.value ? ` (currently '${e.value}')` : ""}${where}`, { type: "fill", id: e.id, text: String(v) }); } }
  }
  if (state.scrollY + state.viewportHeight < state.pageHeight - 20) { add("scroll_down", "Scroll down one screen to see more of the page", { type: "scroll", dy: 1 }); add("scroll_bottom", "Jump to the very bottom of the page", { type: "jump", to: "bottom" }); }
  if (state.scrollY > 0) { add("scroll_up", "Scroll up one screen", { type: "scroll", dy: -1 }); add("scroll_top", "Jump to the top of the page", { type: "jump", to: "top" }); }
  add("wait", "Wait a moment for the page to change", { type: "wait" });
  if (!task.noDone) add("done", "The goal is already accomplished; stop", { type: "done" });
  return { opts, acts };
}

// ---------- TypeSafe ----------
export async function decide(state, task, history, change, opts) {
  const body = {
    state: { goal: task.goal, planner_hint: task.hint || "", data_available_to_type: task.data || {}, what_just_changed: change, recent_actions: history.slice(-4), page: state },
    model: "jev-latest",
    questions: {
      next: { type: "choice", instructions: "You are operating a web browser to accomplish the goal. Given the page state, what just changed, and the recent actions, which single action should be taken next? Prefer the action that makes progress toward the goal; choose 'done' only if the goal is already accomplished.", criteria: opts },
      complete: { type: "noul", instructions: "Has the goal already been accomplished? Judge from the current page state; a visible confirmation, thank-you, or 'received' status message after a submission means yes." },
      blocked: { type: "noul", instructions: "Is progress blocked by something that needs a human, such as a login, a captcha, a payment, or an error message?" },
    },
  };
  const t = performance.now();
  const r = await fetch("https://api.typesafe.ai/v1/systemone", { method: "POST", headers: { Authorization: `Bearer ${KEY}`, "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const j = await r.json(); if (!r.ok) throw new Error("typesafe " + r.status + " " + JSON.stringify(j).slice(0, 200));
  return { ms: performance.now() - t, answers: j.answers, usage: j.usage };
}

// ---------- executor ----------
export const sleep = (ms) => new Promise(r => setTimeout(r, ms));
export async function center(cdp, id) { await cdp.eval(`(() => { const el = document.querySelector('[data-fl="${id}"]'); if (el) el.scrollIntoView({ block: 'nearest', inline: 'nearest' }); })()`); await sleep(40); return cdp.eval(`(() => { const el = document.querySelector('[data-fl="${id}"]'); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; })()`); }
export async function act(cdp, a) {
  if (a.type === "click") { const c = await center(cdp, a.id); if (!c) throw new Error("element gone"); await sleep(60); for (const type of ["mouseMoved", "mousePressed", "mouseReleased"]) await cdp.send("Input.dispatchMouseEvent", { type, x: c.x, y: c.y, button: "left", clickCount: 1 }); }
  else if (a.type === "fill") { const c = await center(cdp, a.id); if (!c) throw new Error("element gone"); for (const type of ["mousePressed", "mouseReleased"]) await cdp.send("Input.dispatchMouseEvent", { type, x: c.x, y: c.y, button: "left", clickCount: 1 }); await cdp.eval(`(() => { const el = document.querySelector('[data-fl="${a.id}"]'); el.focus(); el.select && el.select(); })()`); await cdp.send("Input.insertText", { text: a.text }); }
  else if (a.type === "select") { await cdp.eval(`(() => { const el = document.querySelector('[data-fl="${a.id}"]'); el.selectedIndex = ${a.index}; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); })()`); }
  else if (a.type === "scroll") { await cdp.send("Input.dispatchMouseEvent", { type: "mouseWheel", x: 400, y: 400, deltaX: 0, deltaY: a.dy * 600 }); }
  else if (a.type === "jump") { await cdp.eval(a.to === "bottom" ? "window.scrollTo(0, document.body.scrollHeight)" : "window.scrollTo(0, 0)"); }
  else if (a.type === "wait") { await sleep(500); }
}
export async function settle(cdp) { let last = null; const t = performance.now(); while (performance.now() - t < 1500) { await sleep(last === null ? 80 : 60); const s = await cdp.eval(STATE_JS); const k = sig(s); if (s.ready === "complete" && k === last) return s; last = k; } return cdp.eval(STATE_JS); }

// ---------- planner fallback (Claude, headless) ----------
import { execFile } from "node:child_process";
export async function plan(task, state, history, reason) {
  const prompt = `You are the planner for a fast browser agent that can only click, type provided data, choose dropdown options, and scroll. It escalated to you because: ${reason}.\nGoal: ${task.goal}\nData it may type: ${JSON.stringify(task.data || {})}\nRecent actions: ${JSON.stringify(history.slice(-6))}\nPage: ${JSON.stringify({ url: state.url, title: state.title, headings: state.headings, status: state.status, dialogOpen: state.dialogOpen, elements: state.elements.slice(0, 40), text: state.textSample.slice(0, 500) })}\nReply with exactly one JSON object and nothing else: {"needs_human": boolean, "reason": "one sentence", "hint": "one concrete instruction for the next few actions, or empty"}. Set needs_human true only if a login, captcha, payment, or an error genuinely requires a person.`;
  const t = performance.now();
  const out = await new Promise((res, rej) => execFile(`${process.env.HOME}/.local/bin/claude`, ["-p", "--model", "sonnet", "--output-format", "json", "--max-turns", "1", prompt], { timeout: 90000, maxBuffer: 1 << 20 }, (e, so) => e ? rej(e) : res(so)));
  let text = ""; try { text = JSON.parse(out).result || ""; } catch { text = out; }
  const m = text.match(/\{[\s\S]*\}/); let j = { needs_human: false, reason: "unparsed", hint: "" }; try { j = JSON.parse(m ? m[0] : text); } catch {}
  return { ...j, ms: Math.round(performance.now() - t) };
}

// ---------- loop ----------
export async function run(task, existing) {
  const cdp = existing || await connect(task.urlMatch);
  if (task.url) { await cdp.send("Page.navigate", { url: task.url }); await sleep(800); }
  let prev = null, state = await settle(cdp); const history = []; const log = []; let totalTokens = 0, totalOut = 0, escalations = 0; const t0 = performance.now(); const initialStatus = new Set(state.status);
  for (let step = 1; step <= MAX_STEPS; step++) {
    const tObs = performance.now(); state = await cdp.eval(STATE_JS); const change = diff(prev, state); const obsMs = performance.now() - tObs;
    for (const m of (state.textSample.match(/\b\d{4,8}\b/g) || [])) { task._seen = task._seen || []; if (!task._seen.includes(m) && task._seen.length < 5) task._seen.push(m); }
    if ((task.untilUrl && state.url.includes(task.untilUrl)) || (task.untilText && state.textSample.includes(task.untilText))) { log.push({ step, observe_ms: Math.round(obsMs), decide_ms: 0, tokens: 0, options: 0, choice: '(condition met)', confidence: 1, complete: 1, blocked: 0, top: '', result: 'DONE' }); break; }
    const { opts, acts } = buildOptions(state, task);
    const d = await decide(state, task, history, change, opts); totalTokens += d.usage.input_tokens; totalOut += d.usage.output_tokens || 0;
    const a = d.answers; const choice = a.next.choice; const conf = a.next.confidence; const top = Object.entries(a.next.probabilities).sort((x, y) => y[1] - x[1]).slice(0, 3).map(([k, v]) => `${k}:${v.toFixed(2)}`).join(" ");
    const row = { step, observe_ms: Math.round(obsMs), decide_ms: Math.round(d.ms), tokens: d.usage.input_tokens, options: Object.keys(opts).length, choice: opts[choice], confidence: +conf.toFixed(2), complete: +a.complete.noul.toFixed(2), blocked: +a.blocked.noul.toFixed(2), top };
    const newStatus = state.status.filter(s => !initialStatus.has(s));
    if ((task.untilUrl && state.url.includes(task.untilUrl)) || (task.untilText && state.textSample.includes(task.untilText))) { log.push({ step, observe_ms: Math.round(obsMs), decide_ms: 0, tokens: 0, options: 0, choice: '(condition met)', confidence: 1, complete: 1, blocked: 0, top: '', result: 'DONE' }); break; }
    if (!task.noDone && (a.complete.noul > 0.85 || choice === "done" || (a.complete.noul > 0.6 && newStatus.length))) { row.result = "DONE"; log.push(row); break; }
    task._tried = task._tried || {}; task._tried[choice] = (task._tried[choice] || 0) + 1;
    const why = a.blocked.noul > 0.7 ? "blocked" : conf < MIN_CONF ? "low confidence" : null;
    if (why) {
      escalations++;
      if (escalations > 2) { row.result = "STOP: too many escalations"; log.push(row); break; }
      const p = await plan(task, state, history, why); row.planner = { ms: p.ms, needs_human: p.needs_human, reason: p.reason, hint: p.hint };
      if (p.needs_human) { row.result = `NEEDS HUMAN: ${p.reason}`; log.push(row); break; }
      task.hint = p.hint; history.push(`[planner hint] ${p.hint}`); row.result = `escalated (${why}) -> hint applied`; log.push(row); continue;
    }
    const tAct = performance.now(); try { await act(cdp, acts[choice]); } catch (e) { row.error = e.message; } prev = state; state = await settle(cdp); row.act_ms = Math.round(performance.now() - tAct);
    history.push(opts[choice]); log.push(row);
  }
  const wall = (performance.now() - t0) / 1000;
  if (!existing) cdp.ws.close();
  return { task: task.name, steps: log.length, wall_s: +wall.toFixed(2), tokens: totalTokens, tokens_out: totalOut, final: log[log.length - 1]?.result || "MAX_STEPS", log, finalState: { url: state.url, dialogOpen: state.dialogOpen, status: state.status, text: state.textSample.slice(0, 200) } };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const task = JSON.parse(readFileSync(process.argv[2], "utf8"));
  const r = await run(task);
  console.log(`\n== ${r.task}: ${r.final} in ${r.steps} steps, ${r.wall_s}s wall, ${r.tokens} tokens`);
  console.log("step  obs  decide  act   tokens opts conf  done  blk  choice");
  for (const l of r.log) { console.log(`${String(l.step).padStart(4)} ${String(l.observe_ms).padStart(4)} ${String(l.decide_ms).padStart(7)} ${String(l.act_ms ?? "-").padStart(5)} ${String(l.tokens).padStart(7)} ${String(l.options).padStart(4)} ${l.confidence.toFixed(2)}  ${l.complete.toFixed(2)}  ${l.blocked.toFixed(2)}  ${l.choice}${l.error ? "  !" + l.error : ""}${l.result ? "  => " + l.result : ""}`); if (l.planner) console.log(`      planner ${l.planner.ms}ms needs_human=${l.planner.needs_human} reason="${l.planner.reason}" hint="${l.planner.hint}"`); }
  console.log("final:", JSON.stringify(r.finalState));
}
