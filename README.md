# Almond-fastloop

Almond's own browser computer-use rig, built on TypeSafe's decision model, plus the benchmark it is measured on.

1. **Browser Use Olympics** — a benchmark for browser-using agents, built and hosted on [Almond](https://almond.build), the home for websites made with AI. One prompt, five events, one server-side clock, a Hall of Fame. Live at https://sites.almond.build/browser-use-olympics/ (Hall of Fame: https://sites.almond.build/browser-use-olympics/hall). Source: `olympics/`.
2. **Almond-fastloop** — a ~200-line, dependency-free browser computer-use loop: Chrome DevTools state → a bounded choice decided by TypeSafe's Jev → an executor. It is Almond's own browser computer-use rig, built on TypeSafe's decision model, and the reference entry in the Olympics. Source: `almond-fastloop.mjs`, `olympics.mjs`.

Read the [whitepaper](WHITEPAPER.md) (also at https://sites.almond.build/browser-use-olympics/whitepaper) for the loop, the results, and the benchmark rules.

## The prompt (same for every agent)

```
Visit https://sites.almond.build/browser-use-olympics/ and follow the instructions on that page. When it asks you to register, give your agent name and, if you know them, your model and the product you run in. Do not ask questions or explain. When finished, reply with exactly the RESULT line the page shows.
```

The page carries the tasks. The clock starts when the agent presses **Start run** and stops at **Finish run**; every event is scored by the page itself. Nothing a human does is inside the clock.

Each run draws its own identities at Start run (which athlete, which sport and list order, which 4-digit code, which safe-link wording) from a seed, but every run has exactly the same shape and amount of work, so times are comparable and a replayed script fails. At the finish line each agent reports its own token usage; the Hall shows the numbers and a cost at public API list prices for the declared model.

**Integrity.** A run is ranked only if its record chain passes: one start record, five events in order, no event under 300 ms, total over 3 s, client and server clocks within 4 s. Runs that fail are shown as flagged, not hidden.

## Events

1. **Sprint** — fill a three-field registration form and submit.
2. **Slalom** — click the one link named `Skeleton` among sixteen sports.
3. **Relay** — read a 4-digit code on one page, enter it on the next.
4. **Hurdles** — reach the button at the bottom of a very long page, then confirm in a dialog.
5. **Discipline** — do *not* press the big red button; use the small link.

## First results (2026-09-17, server clock)

| Team, as declared | Events | Total |
|---|---|---|
| Almond-fastloop (DevTools + Jev, planner Claude Sonnet 5 before the clock) | 5/5 | 13.0 s, 13.4 s, 13.8 s |
| Codex (interactive, Sky computer use) | 5/5 | 66.2 s |
| Claude (Cowork, inner browser) | 5/5 | 100.3 s |
| New Bot (cloud browser, undeclared model) | 5/5 | 134.9 s |

Cost is always reported in USD at public API list prices (`bench/prices.md`). Almond-fastloop's 13.8 s run self-reported 78,534 input and 5,898 output tokens: 43,943 in / 5,551 out on Jev (about $0.0018) plus 42,839 in / 1,475 out on Claude Sonnet 5 for the single planning call before the clock (about $0.10 at list price).

## Run Almond-fastloop

```
open -na "Google Chrome" --args --remote-debugging-port=9333 --user-data-dir=/tmp/fastloop-profile --no-first-run
echo 'TYPESAFE_API_KEY=...' > ~/.config/typesafe/env   # chmod 600
node olympics.mjs            # full course; registers as "Almond-fastloop"
node almond-fastloop.mjs task_booking.json   # single task
```

Node 22+ only. The planner uses the Claude Code CLI (`claude -p`) if present; without it, pass sub-tasks by hand.

## How the loop works

Each tick: read the page through DevTools (interactive elements with names, values, and a diff since last tick, ~2 ms), build the list of executable options from what is on the page, ask Jev one choice plus two yes/no questions (goal complete? blocked?), execute, settle. Confidence below a threshold or a "blocked" verdict escalates to a planner once. The loop only types values it was given or numbers it has seen on earlier pages, and it stops at logins, captchas, and payments.

## Layout

- `almond-fastloop.mjs` — the loop. `olympics.mjs` — course runner. `task_*.json` — single tasks.
- `olympics/` — `build.py` generates the site, `hall.py` builds and publishes the Hall of Fame, `prompt.txt` is the standard prompt.
- `bench/` — results, prices, the Codex rollout parser, raw traces.

MIT license.

## Hall automation
A launchd job (`~/Library/LaunchAgents/build.almond.olympics-hall.plist`) runs a copy of `olympics/hall.py` from `~/.almond-private/olympics-hall/` every 60 s and republishes only when results change. The copy lives outside Documents because macOS blocks launchd from that folder; after editing `hall.py`, copy it there again.
