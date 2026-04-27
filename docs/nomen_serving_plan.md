# Nomen Serving Plan — Pre-generated Reports (Phase 1)

The cheapest, fastest, and most reliable way to ship Nomen at launch: pre-generate match analysis reports in a daily batch job, cache them as static files, and serve them from FastAPI without any GPU in the request path.

This is the **recommended Phase 1 deployment**. For the live-chat upgrade path (Phase 2), see the bottom of this document.

---

## TL;DR

|  | Pre-generated (Phase 1) | Live chat (Phase 2) |
|---|---|---|
| Cost | **~$10–25/mo** | ~$1,200/mo |
| Latency for user | **~0 ms** (static files) | ~15s per response |
| Concurrent users | unlimited | ~500–1,500 |
| GPU in request path | none | required 24/7 |
| Operational risk | low | medium |

Start with Phase 1. Upgrade to Phase 2 only when there's evidence users want live chat (and you can monetize it).

---

## Architecture

```
[Railway]                                [RunPod, on-demand]

fb snapshot
  ↓
data/snapshots/today.json
  ↓
api/scheduler.py ────── trigger ──────▶  start pod (~3 min cold start)
                                         ↓
                                         batch_nomen_reports.py
                                         ↓ reads today.json
                                         ↓ runs Nomen on each fixture (~45s)
                                         ↓ writes reports/{fixture_id}.md
                                         ↓
                                         stop pod  (billing stops)

[Railway, request path]

GET /predictions/today
  ↓
match_analyst.py reads
  data/snapshots/reports/{fixture_id}.md
  ↓
returns to frontend instantly
```

User flow stays exactly as today: clicks Lazio → sees probabilities + form + Nomen report. The report is just a Markdown file on disk, served like any other field of the API response.

---

## Cost breakdown

Assumptions: 30 fixtures per matchday, ~45s Nomen inference per fixture, A100 80 GB at $1.64/h.

| Schedule | Daily compute | Monthly cost |
|---|---|---|
| Daily refresh (every day) | ~30 min | **~$25** |
| Matchdays only (~4×/week) | ~30 min × 16 days | **~$13** |
| Weekend + midweek only | ~30 min × 12 days | **~$10** |

Compared to persistent A100 ($1,200/mo), Phase 1 is **50–100× cheaper**.

---

## Implementation

### New files

| File | Purpose |
|---|---|
| `scripts/batch_nomen_reports.py` | Reads `today.json`, generates Nomen report per fixture, writes Markdown files |
| `scripts/runpod_lifecycle.py` | Helper: start/stop pod via RunPod API, poll health, hard-timeout safety |
| `data/snapshots/reports/` | Cache directory — one `.md` per `fixture_id` |

### Files to update

| File | Change |
|---|---|
| [src/football_betting/api/scheduler.py](../src/football_betting/api/scheduler.py) | After `today.json` refresh: `runpod_lifecycle.start()` → run batch job → `stop()` |
| [src/football_betting/support/match_analyst.py](../src/football_betting/support/match_analyst.py) | Replace live LLM call with file read from `data/snapshots/reports/{fixture_id}.md`; clean fallback to `None` when file missing |
| [src/football_betting/api/routes.py](../src/football_betting/api/routes.py) | Extend `/predictions/today` response with `nomen_report: str \| None` field |
| [web/lib/types.ts](../web/lib/types.ts) | Add `nomen_report: string \| null` to fixture type |
| `web/lib/i18n/{locale}.ts` | UI strings: report section header, "Analysis loading…" fallback |

### Schema for a cached report

`data/snapshots/reports/{fixture_id}.md`:

```markdown
---
fixture_id: 12345
league: SA
home: Lazio
away: Udinese
kickoff: 2026-04-27T20:45:00Z
generated_at: 2026-04-27T06:15:32Z
nomen_version: v1
inputs_hash: a3f9c1
---

Lazio kommt mit drei Siegen in Folge — defensiv stabil, in der Box brutal effizient. Udinese …
```

The frontmatter lets us detect stale reports: if `inputs_hash` no longer matches the current `today.json` inputs, that fixture is dirty and gets re-generated.

---

## Re-generation strategy

Reports are not statically valid all day — odds shift and team news breaks. Three-tier refresh:

1. **Daily full batch (06:00 UTC)** — regenerate everything from scratch.
2. **Hash check on every `fb snapshot`** — if a fixture's inputs changed materially (probability moved >3 pp, value-bet flag flipped, lineup news arrived), mark it dirty.
3. **Mini-batches at 12:00 and 17:00 UTC** — only re-run Nomen on dirty fixtures. Typically 2–5 of 30 → ~5 min of pod time.

Adds ~$5/mo on top of the daily batch and keeps reports fresh for kickoff.

---

## Failure modes

| Failure | User impact | Mitigation |
|---|---|---|
| RunPod down at batch time | Yesterday's report shown | Frontmatter shows `generated_at` — frontend can render an "Updated yesterday" badge |
| Nomen hallucinates (wrong score, off-topic) | One bad report served all day | Reuse `validate_nomen_dataset.py` heuristics inline — reject reports missing team names or in wrong language; serve `None` instead |
| Hash logic wrong → reports stale | Reports drift from actual probabilities | Daily full regen at 06:00 UTC catches everything |
| Pod doesn't stop | Billing runs forever | `batch_nomen_reports.py --max-runtime 3600` hard-stops after 1h; scheduler also fires `stop` in a `finally` block |
| Snapshot empty (no fixtures) | Skip batch | Early-exit before starting the pod |

---

## Phase 2 — Live chat upgrade path

When (if) live chat becomes a requirement:

1. Switch from on-demand to persistent pod (~$1,200/mo).
2. Use **Q4_AWQ instead of Q8_0** — same A100, ~40 GB more KV-cache headroom → 3–4× concurrency.
3. Enable vLLM **prefix caching** — identical system prompt across users, ~30 % throughput gain.
4. Add a separate code path in `match_analyst.py` that calls vLLM only when the user explicitly opens a follow-up chat.
5. Keep cached reports as the default surface — chat is purely for "ask Nomen a follow-up".

This hybrid (cached default + on-demand chat) keeps costs bounded by actual user activity, not by an idle 24/7 GPU.

---

## Implementation order

1. Create `data/snapshots/reports/` and lock down the file schema (frontmatter + body).
2. Build `scripts/batch_nomen_reports.py` against **local Ollama** first (no RunPod) — generate one fixture, verify Markdown output, iterate on the prompt.
3. Wire `match_analyst.py` to read from the cache, with a clean `None` fallback when the file is missing.
4. Extend `routes.py` and `web/lib/types.ts` so the frontend receives the report.
5. Add `scripts/runpod_lifecycle.py` and integrate it into `scheduler.py` (with `try/finally` to guarantee pod stop).
6. Run end-to-end on one real matchday. Verify actual cost in the RunPod console matches the estimate.
7. Add hash-based mini-batch refresh at 12:00 and 17:00 UTC.

---

## File reference

| File | Purpose |
|---|---|
| [docs/nomen_training_plan.md](nomen_training_plan.md) | One-time training pipeline (this is the prerequisite) |
| `scripts/batch_nomen_reports.py` | Daily/mini batch report generator |
| `scripts/runpod_lifecycle.py` | RunPod start/stop helper with timeout safety |
| `data/snapshots/reports/{fixture_id}.md` | One pre-generated report per fixture |
| [src/football_betting/support/match_analyst.py](../src/football_betting/support/match_analyst.py) | Reads cache, returns report to API |
| [src/football_betting/api/scheduler.py](../src/football_betting/api/scheduler.py) | Triggers batch job after each snapshot refresh |
