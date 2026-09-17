# Almond-fastloop and the Browser Use Olympics

*Ernesto Riestra, Almond · September 17, 2026 · v1.1*

## Abstract

Computer-use agents today look at screenshots and ask a frontier language model what to do next. Each step costs seconds and thousands of tokens. We show that most of a browser task does not need that. Almond-fastloop reads the live page through Chrome's DevTools protocol, turns it into a short list of executable actions, and asks a calibrated decision model, TypeSafe's Jev, to pick one. A step takes well under a second and costs a fraction of a cent. On a five-event course the loop finished in 13.0 to 13.8 seconds where Codex took 54 to 75, Claude Cowork 64, and a Grok-based agent 218. On a single booking form it was 60 to 80 times faster and roughly 4,000 times cheaper than Codex with its Sky computer-use plugin. The Browser Use Olympics is the benchmark we built to make those numbers checkable by anyone: one prompt, one page that carries the tasks, one server-side clock, and a Hall of Fame in which every agent declares itself and reports its own tokens.

## 1. The problem

The dominant design for computer use is a loop of screenshot, reasoning, action. It works, and it is general, but it has a fixed cost per step that no amount of engineering around it removes: a large model must look at an image and produce a plan, every time. We measured that cost on the same task, a three-field booking form on a public page:

| Stack | Wall time | Steps | Cost at API list price |
|---|---|---|---|
| Codex with Sky computer use (interactive, GPT-5.6 Sol) | 279 s | 74 tool calls | $1.80 |
| Claude Cowork (inner browser) | 48 s incl. one permission prompt | 7 browser actions, 3 to 4 model turns | about $0.20 to $0.30, estimated |
| Almond-fastloop | 3.5 to 4.4 s, three runs | 6 to 7 decisions | $0.0005 |

Codex spent nineteen seconds discovering its own tools before touching the page, took a screenshot and a full accessibility tree after almost every action, and needed a model turn of 2.6 to 7.7 seconds for each of 74 calls. Cowork was six times faster because it reads a structured tree and batches actions, but each decision was still a frontier-model turn.

## 2. The idea

TypeSafe's Doom demo showed a model playing the game at ten decisions per second by receiving the engine's variables, health, ammo, enemies with distance and angle, and choosing a tactical macro. It never saw a pixel. A browser has an engine too. Chrome will hand over the DOM and accessibility tree in a few milliseconds. The question was whether the same shape, structured state in, bounded choice out, would hold for real web tasks.

Three properties make it hold:

- **The state is small and named.** Not the whole page, only what can be acted on, with the names a person would see, plus what changed since the last look.
- **The choice is bounded and executable.** The model never invents an action. It picks from a list built from what is actually on the page, so there is nothing to hallucinate from.
- **The decision model is fast and calibrated.** Jev returns a choice, a probability for every option, and a confidence, in 100 to 300 milliseconds, at 4.2 cents per million input tokens. Confidence is what lets the loop know when to stop and ask for help.

## 3. Almond-fastloop

The loop is about two hundred lines of JavaScript with no dependencies beyond Node 22. Each tick:

1. **Observe.** A script injected through DevTools walks the DOM for interactive elements: links, buttons, inputs, selects, text areas, and elements with interactive roles. For each it records role, accessible name, current value, options for a select, and whether it is in the viewport. It also records the URL, title, headings, status messages, values the page shows in code formatting, and a short text sample. If a dialog is open, only the dialog is considered. Elements are tagged with a fresh id each tick, and stale tags are cleared. This costs 2 to 4 milliseconds.
2. **Diff.** The loop compares with the previous tick and produces a sentence: a dialog opened, a field is now filled, the page navigated, nothing changed. A model that never sees pixels has to be told what just happened.
3. **Build options.** Click this button, choose this option in this dropdown, type this value into this field, scroll one screen, jump to the bottom, wait, done. Values to type come from three sources only: what the task provided, what the page currently shows in code formatting, and 4-to-8-digit numbers seen on earlier pages of the run. Options already tried twice without effect are dropped.
4. **Decide.** One call to Jev with the goal, the diff, the recent actions, the compact state, and the option list as a choice question, plus two yes/no questions: is the goal already complete, is progress blocked by something that needs a person. All three are answered in the same call.
5. **Act and settle.** Real mouse and keyboard events through DevTools, then a short poll until the page signature stops changing, usually 200 to 600 milliseconds.
6. **Route on confidence.** Below a threshold, or when the blocked question fires, the loop escalates once to a planner, Claude Sonnet 5 through the Claude Code CLI, which returns either a one-line hint or a verdict that a human is needed, for example a login. A leg ends when the page navigates or when a named text appears, never on the model's opinion alone.

On the Olympics no planner is needed at all: each page states its own instructions, Jev reads them in the page text and picks the action. Every decision, before and inside the clock, is Jev. The planner remains available as the escalation path.

Three safety properties follow from the design rather than from prompting. The loop can only do what the page offers. It only types values it was given or has seen. It stops at logins, captchas, and payments because the blocked question is asked on every tick.

## 4. Results

### 4.1 Single task: booking form

Same page, same three values, all stacks succeeded. See the table in section 1. The loop's three runs were within 0.9 seconds of each other. Its per-step profile was 2 to 3 milliseconds to observe, 240 to 800 milliseconds to decide, and about 600 milliseconds to act and settle, most of the last being a conservative settle timer.

### 4.2 The Olympics course

Five events, server clock from Start run to Finish run, every event scored by the page. All runs below passed all five events.

| Team, as declared | Total | Tokens, self-reported | Cost at list price |
|---|---|---|---|
| Almond-fastloop, no planner | 12.6 s | 48,659 in / 6,015 out on Jev, nothing else | about $0.002 |
| Almond-fastloop, with a Sonnet planning call before the clock | 13.0 s, 13.4 s, 13.8 s, 14.1 s | about 44,000 in / 5,600 out on Jev, plus about 40,000 in / 1,500 out on Sonnet | about $0.002 on Jev plus about $0.10 for planning |
| Codex-tracked | 53.6 s | as declared | as declared |
| Claude Cowork (Fable 5.1) | 64.4 s | 100,000 in / 4,500 out, estimated by the agent | $1.23 |
| Codex (GPT-5) | 73.0 s, 75.0 s | not reported | — |
| Yeira Bot (Grok, Grokbot in Cursor) | 218.3 s | not reported | — |

The loop's event splits were 2.5 s for the form, 1.2 s for the link among sixteen, 0.7 plus 1.8 s for reading a code and entering it on the next page, 2.1 s for the long scroll and dialog, 1.2 s for leaving the red button alone, and 0.6 s to finish. Twenty-three to twenty-seven decisions per run.

### 4.3 What the numbers say

Structured state closes most of the gap: Codex to Cowork is roughly six to one. Replacing the frontier model in the decision seat closes the rest: Cowork to the loop is another five to ten to one on time and hundreds to one on cost. The loop is not smarter than either. It never asks a question larger than "which of these."

## 5. The benchmark

A result like this attracts skeptics, and it should. The Browser Use Olympics exists so that anyone can check it, extend it, and argue with it.

**One prompt.** Every agent receives the same line: visit the page and follow its instructions, register with your own name and model, report your tokens at the finish, reply with the RESULT line. The page carries the tasks, so the prompt cannot favor a stack.

**One clock, on the server.** The clock starts when the agent presses Start run and stops at Finish run. Both are records written by Almond when they arrive. Nothing a human does, and nothing an agent does before it presses Start, is inside the clock.

**Five events, scored by the page.** A three-field form, one link among sixteen, a code read on one page and entered on the next, a button at the bottom of a long page with a confirmation dialog, and a red button that must not be pressed. They cover typing, selecting, finding, carrying state across pages, scrolling, dialogs, and restraint.

**Same shape, different identities.** At Start run each run draws its own athlete, sport, list order, code, and safe-link wording from a seed. Every run has exactly the same number of fields, links, hurdles, and pages, so times are comparable, but a script that replays a previous run fails on three of five events.

**Integrity checks.** A run is ranked only if its record chain has one start, five events in order, no event under 300 milliseconds, a total over 3 seconds, and client and server clocks within 4 seconds. Failing runs are shown, flagged, not hidden.

**Self-reported tokens, priced at list.** Each agent reports its input and output tokens at the finish line and says where the numbers came from. The Hall shows them and a cost at the declared model's public API list price, uncached input rate. "Subscription" is never accepted as a cost.

**Self-declared identity.** The Hall shows what each agent typed as its name, model, and harness. When an agent registered as "Yeira Bot" with model "Grok," that is what the board says.

**A verified tier.** The event endpoint is public, so a record chain can be forged. A run is marked verified when its trace, a transcript, rollout, or loop log, is submitted to the repository naming the run id. Unverified rows stay on the board, marked.

**The whole thing runs on Almond.** The site, its pages, the records, and the Hall were created through Almond's agent contract in about three and a half minutes from the first line of code, with no build step and no deploy. That is a small demonstration of the other half of the thesis: a website that is structured for agents is fast to make and fast to operate.

## 6. Limitations

- **No vision.** Canvas applications, image-only content, and visual captchas have no usable tree. The loop escalates to the planner or stops. A vision model can be added as a fallback; it is not in the loop today.
- **A planner, when used, dominates cost.** One Sonnet call costs about fifty times the Jev spend of a run, almost all of it the CLI's own context rather than the page. On the Olympics the loop now runs without one; on open-ended tasks it is still the escalation path, and its cost should be reported whenever it fires.
- **Small samples.** Three loop runs on the course, one or two for each other stack. The direction is not in doubt; the decimals are.
- **Self-reported tokens.** Two stacks reported estimates, two reported nothing. The rule is honest about that; it is still weaker than a metered number.
- **Forgeable records** until the verified tier has traces behind it.
- **The Hall refresh runs on a laptop.** Almond has no way yet for a page to read its own records or to regenerate itself on a schedule. That is a platform feature to build, and until then the leaderboard updates only while one machine is awake.
- **One leg per page.** The course runner ends a leg on navigation. Tasks that stay on one page across many states need the end conditions written differently.

## 7. What is ours and what is borrowed

Ours: the state builder, the diff, the option builder, the executor, the settle logic, the run-level memory, the end conditions, the escalation, the course runner, the benchmark site, the integrity rules, and the Hall. Borrowed and replaceable: Chrome's DevTools protocol for state and input, TypeSafe's Jev for the decision, Claude for the occasional plan. Almond-fastloop is Almond's own browser computer-use rig, built on TypeSafe's decision model. Said that way, it is neither overclaimed nor underclaimed.

## 8. Reproducing

Launch Chrome with a debugging port and a throwaway profile, put a TypeSafe key in a private file, and run the course runner. Every run writes its decisions, timings, and tokens to a trace file. The repository holds the loop, the course runner, the site generator, the Hall builder, the standard prompt, the price table, and the results, under the MIT license: https://github.com/eriestra/almond-fastloop. The benchmark is at https://sites.almond.build/browser-use-olympics/.

## 9. What comes next

An event pool whose variants are measured equivalent before they enter, so the course can grow without adding time or complexity variance. Traces behind every ranked row. The Hall regenerated on Almond itself. A cheaper planner, or none, for courses whose instructions are simple enough for Jev to read directly. Adapters that run other stacks under the same clock: Claude in Chrome, Codex with Sky, Playwright with a language model. And the obvious next benchmark: the same loop on desktop applications through the operating system's accessibility tree, which is exactly the state Sky already produces.
