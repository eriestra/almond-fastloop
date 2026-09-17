# Results — booking-v1

| run | stack | model | prompt | start | record | RESULT | steps | tokens | cost (list) | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-17 08:54 | Codex + Sky (interactive) | gpt-5.6-sol low | v0 (Sky bootstrap wording) | 08:54:38 | — | 08:59:16 (278.7 s) | 74 tool calls | 68,512 uncached + 2,425,088 cached in; 8,052 out | $1.80 | rollout parsed; 18.9 s before first browser action |
| 2026-09-17 ~00:30 | Fast loop (DevTools + Jev) | jev-1.13.0 | v0 goal | — | — | 3.54 / 4.25 / 4.35 s | 6–7 | ~11,000 in | $0.0005 | 3 runs, all done |
| 2026-09-17 09:14 | Claude Cowork (inner browser) | Claude desktop default (model to confirm) | v1 | 09:14:31.07 (GO) | 09:15:19.36 (48.3 s) | ~09:15:25, from screenshot | 7 browser actions in ~3–4 model turns; read_page missed the form fields, fell back to JS | not reported; estimated 110–130k in (mostly cached after turn 1), ~1.5k out | est. $0.20 (Opus 5) – $0.30 (Fable 5.1) | includes one inner-browser permission prompt; record values correct |

## Browser Use Olympics — build log
- 2026-09-17 09:19 first line of `olympics/build.py` written; 09:22:38 site created on Almond (`app_create`, owned at creation); seven event pages live by 09:22:45; 09:23:35 registration/identity revision republished; 09:24:15 Hall of Fame page live. **First line of code to a live 8-page logging site: ~3.5 min; with Hall of Fame: ~5 min.** No deploy, no build step, one Convex-backed publish per page.
