# booking-v1 — standard task

- Page: https://sites.almond.build/almond-demo-taller-barrio/ (Entre Barro demo; form creates a record in collection `interests`; no real booking)
- Prompt: the exact text in `booking-v1.prompt.txt`, pasted verbatim into every stack. No extra hints, no stack-specific wording. (The 2026-09-17 08:54 Codex+Sky run used an earlier variant with Sky bootstrap instructions; it is marked "prompt v0" in results.)
- Data: nombre = "Visitante de prueba"; taller = "Modelado a mano"; horario = "Sábado".
- Success: the page shows "Solicitud de prueba recibida…" and a new `interests` record exists.
- Clock: starts when the user presses enter on the prompt; stops when the record is created (watcher timestamp) and, separately, when the RESULT line appears.
- Recorded per run: stack, model(s), prompt version, start time, record time, RESULT time, steps/tool calls, tokens, cost, traces path.
- Cost rule: ALWAYS in equivalent USD at the model's public API list price (input, cached input, output), dated in `prices.md`. Subscription-billed stacks are converted the same way; "subscription" is never an accepted cost entry. When a stack does not report tokens, tokens are estimated from its transcript (turns × context size, screenshots at the vendor's published per-image token rule) and the row is marked "estimated" with the method.
- Fast loop mapping: task_booking.json goal must equal the prompt's first two sentences; data keys map to the three fields.
