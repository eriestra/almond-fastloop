// Browser Use Olympics runner for the fast loop.
// Prompt to every stack is the same one line; this runner reads the instructions from the page,
// asks the planner (Claude, headless) once to turn them into sub-tasks, registers, then runs the loop per page.
import { connect, STATE_JS, run, sleep } from "./almond-fastloop.mjs";
import { execFile } from "node:child_process";
import { writeFileSync } from "node:fs";

const START = process.env.BUO_URL || "https://sites.almond.build/browser-use-olympics/";
const IDENTITY = { team: process.env.BUO_TEAM || "Almond-fastloop", model: "jev-latest", harness: "Almond-fastloop: DevTools+Jev, planner claude-sonnet-5" };

const planUsage = { in: 0, out: 0 };
async function planCourse(state) {
  const links = state.elements.filter(e => e.role === "link").map(e => e.name);
  const prompt = `You are planning for a fast browser agent that can click, type provided values, choose dropdown options, scroll, and confirm dialogs. It also remembers 4-8 digit numbers it has seen on earlier pages and can type them. It runs one sub-task per page; a sub-task ends when the browser navigates to a new page, or when a given text appears.
Here are the instructions of a benchmark course, as page text:
---
${state.textSample.slice(0, 2500)}
---
Links on the page: ${JSON.stringify(links)}
Produce the ordered list of sub-tasks AFTER registration (registration is handled separately). One sub-task per page visit. For each: "name", "goal" (one imperative sentence naming the exact values or links to use, and ending with the navigation to the next page), "data" (object of field name -> LITERAL value to type, copied exactly from the instructions; use {} when nothing is typed on that page; NEVER write placeholders such as "<code>" — values that must be read from an earlier page are remembered automatically, so leave them out of data), and optionally "untilText" for the final page (the text that appears when done). Reply with exactly one JSON array and nothing else.`;
  const out = await new Promise((res, rej) => execFile(`${process.env.HOME}/.local/bin/claude`, ["-p", "--model", "sonnet", "--output-format", "json", "--max-turns", "1", prompt], { timeout: 120000, maxBuffer: 1 << 20 }, (e, so) => e ? rej(e) : res(so)));
  let text = "", usage = {}; try { const j = JSON.parse(out); text = j.result || ""; usage = j.usage || {}; } catch { text = out; }
  planUsage.in = (usage.input_tokens || 0) + (usage.cache_read_input_tokens || 0) + (usage.cache_creation_input_tokens || 0); planUsage.out = usage.output_tokens || 0;
  const m = text.match(/\[[\s\S]*\]/); const course = JSON.parse(m ? m[0] : text);
  for (const c of course) { c.data = Object.fromEntries(Object.entries(c.data || {}).filter(([k, v]) => typeof v === "string" && v.trim() && !/[<>]|remember|placeholder|read from|seen on/i.test(v))); }
  return course;
}

const t0 = performance.now();
const cdp = await connect("browser-use-olympics");
await cdp.send("Page.navigate", { url: START + "?new=1" }); await sleep(900);
let state = await cdp.eval(STATE_JS); state.textSample = await cdp.eval("document.body.innerText.replace(/\\s+/g,' ').slice(0, 4000)");
const tPlan = performance.now(); const course = await planCourse(state);
if (course.length < 6) { console.log("planner returned only", course.length, "sub-tasks; aborting"); cdp.ws.close(); process.exit(2); } const planMs = Math.round(performance.now() - tPlan);
console.log(`plan (${planMs} ms, before the clock):`); for (const c of course) console.log("  -", c.name, "|", c.goal.slice(0, 110), "|", JSON.stringify(c.data || {}));
if (process.env.BUO_PLAN_ONLY) { console.log(JSON.stringify(course, null, 1)); cdp.ws.close(); process.exit(0); }

if (course.length < 6) { console.log('planner returned only', course.length, 'sub-tasks; aborting before the clock starts'); cdp.ws.close(); process.exit(2); }
course[course.length - 1].untilText = 'RESULT: run';
const results = []; const memory = []; // values seen on earlier pages, shared across sub-tasks
// Registration: identity is our own; clock starts when Start run is pressed.
results.push(await run({ name: "register", goal: `Register the team: type the team, model and harness values into the registration form and press 'Start run'.`, data: IDENTITY, untilUrl: "/e1", noDone: true, _seen: memory }, cdp));
for (const c of course) {
  const task = { name: c.name, goal: c.goal, data: c.data || {}, untilText: c.untilText, noDone: true, _seen: memory };
  if (c === course[course.length - 1]) { const tin = planUsage.in + results.reduce((a, r) => a + r.tokens, 0), tout = planUsage.out + results.reduce((a, r) => a + (r.tokens_out || 0), 0); task.data = { tokens_in: String(tin), tokens_out: String(tout), tokens_note: "Jev usage from API responses + one Claude planning call; excludes this finish leg" }; task.goal = `Type the token numbers into the three token fields (input tokens ${tin}, output tokens ${tout}, source note), then press 'Finish run'.`; }
  if (!task.untilText) task.untilUrl = null; // ends on navigation: detect by URL change from current
  const before = (await cdp.eval("location.href"));
  task.untilUrlChangeFrom = before;
  results.push(await runUntilNav(task, before));
}
const finalText = await cdp.eval("(document.getElementById('r')||{}).textContent||''");
const total = ((performance.now() - t0) / 1000).toFixed(1);
console.log("\nRESULT:", finalText || "(no result line)");
console.log(`sub-tasks: ${results.length}  decisions: ${results.reduce((a, r) => a + r.log.filter(l => l.decide_ms > 0).length, 0)}  jev tokens: ${results.reduce((a, r) => a + r.tokens, 0)} in / ${results.reduce((a, r) => a + (r.tokens_out || 0), 0)} out  planner: ${planUsage.in} in / ${planUsage.out} out  local wall incl. planning: ${total}s`);
for (const r of results) console.log(`  ${r.task.padEnd(12)} ${r.final.padEnd(10)} ${r.steps} steps ${r.wall_s}s ${r.tokens} tok`);
writeFileSync(`bench/olympics_fastloop_${Date.now()}.json`, JSON.stringify({ identity: IDENTITY, planMs, course, results, finalText }, null, 1));
cdp.ws.close();

async function runUntilNav(task, fromUrl) {
  // a sub-task ends when the URL changes from fromUrl (or untilText appears)
  const t = { ...task, untilUrl: null };
  const origEval = cdp.eval.bind(cdp);
  // wrap: inject a synthetic untilUrl check by polling URL inside run via untilText fallback
  t._fromUrl = fromUrl;
  // almond-fastloop run supports untilUrl (substring) only; emulate "changed" with a sentinel handled below
  return runWithNavWatch(t, fromUrl);
}
async function runWithNavWatch(task, fromUrl) {
  // run() checks task.untilUrl as a substring of state.url; we cannot express "different from", so we
  // give run() a getter that becomes truthy once the URL differs.
  Object.defineProperty(task, "untilUrl", { get() { return task.__nav ? task.__navUrl : null; }, configurable: true });
  const poll = setInterval(async () => { try { const u = await cdp.eval("location.href"); if (u !== fromUrl && !task.__nav) { task.__nav = true; task.__navUrl = u; } } catch {} }, 100);
  try { return await run(task, cdp); } finally { clearInterval(poll); }
}
