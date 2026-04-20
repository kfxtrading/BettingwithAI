# Chatbot-Erweiterung zu kleinem LLM — Verfeinerter Plan (Ansatz A)

Status: **Draft** · Owner: Marcel · Zielversion: next minor bump in `pyproject.toml` + CHANGELOG

## 1. Kontext & Ist-Zustand

Der aktuelle Support-Chatbot (`web/components/SupportChat.tsx`) ist **kein LLM**, sondern eine reine
Fuse.js-Fuzzy-Suche über statische FAQ-Einträge (`web/lib/faq.ts`). Schwächen:

- Nur fuzzy-passende FAQ-Treffer, kein Sprachverständnis.
- Kein Kontext zu Liga, aktuellem Spiel, Odds, Value Bets.
- Keine Mehrschritt-Dialoge, keine Domänenlogik, keine Tool-Nutzung.

## 2. Zielbild

Ein domänenspezifischer Chatbot, der:

1. Fragen zum Projekt (Pi-Ratings, Dixon-Coles, Kelly, Value Bets, Backtests) beantwortet.
2. Live-Daten aus der FastAPI (`/api/today`, `/api/matches/...`) via **Tool-Calling** liest.
3. Mehrsprachig antwortet (DE / EN / FR / ES / IT — passend zur bestehenden i18n).
4. Innerhalb eines Monatsbudgets von **50 €** läuft, ohne Qualitätsabfall.

## 3. Architekturentscheidung — Ansatz A: Azure OpenAI + RAG

| Punkt | Wahl | Begründung |
|---|---|---|
| **Generator-Modell** | `gpt-4o-mini` via Azure OpenAI | ~$0.15 / 1M in, $0.60 / 1M out → ~100 k Chats für 50 € |
| **Embedding-Modell** | `text-embedding-3-small` (1536-dim) via Azure OpenAI | einmaliger Index-Build unter 0,05 € |
| **Vektor-Store** | **FAISS** lokal unter `data/rag_index/` | keine Azure-AI-Search-Kosten, reicht für < 10 k Chunks |
| **Hosting** | Bestehende FastAPI auf **Railway** erweitern | kein neuer Service, keine Zusatzkosten |
| **Streaming** | SSE über `POST /api/chat` | nativ in FastAPI + fetch-Stream im Frontend |
| **Sprachen** | DE / EN / FR / ES / IT, System-Prompt pro Locale, Chunks sprach-getaggt | alle 5 bestehenden Locales ab Tag 1 |

## 4. Budget-Kalkulation (50 €)

- **Index-Build** (einmalig): ~0,05 €.
- **Pro Anfrage**: avg 2k Input + 300 Output Tokens ≈ 0,0005 €.
- **50 €** ≈ **100 000 Chat-Antworten** — deutlich über Bedarf.
- **Safety-Buffer**: Rate-Limit 20 Anfragen / IP / h + Azure-Monthly-Budget-Alert bei 40 €.

## 5. Umsetzungsschritte

### 5.1 Python-Modul `src/football_betting/llm/`

- `corpus.py` — sammelt Chunks aus:
  - `README.md`, `CHANGELOG.md`, `web/content/**/*.md`
  - Docstrings aus `predict/`, `betting/`, `rating/`, `features/`
  - FAQ aus `web/lib/faq.ts` (alle 5 Locales)
  - heutige Snapshot-Zusammenfassung aus `data/snapshots/today.json`
- `rag.py` — FAISS-Index bauen / laden, Top-k Retrieval mit Sprach-Filter.
- `tools.py` — Tool-Schema + Python-Handler für
  - `get_today_predictions(league)`
  - `get_match_detail(match_id)`
  - `explain_value_bet(match_id)`
  - `explain_pi_rating(team)`
- `client.py` — Azure OpenAI Client (Key oder Managed Identity, Endpoint aus ENV).
- `chat.py` — Orchestrator: Retrieve → locale-aware System-Prompt → `gpt-4o-mini` mit Tool-Calling → Stream.

### 5.2 CLI

- Neuer Click-Befehl `fb rag-build` in `src/football_betting/cli.py`
  (baut bzw. aktualisiert FAISS-Index inkrementell).

### 5.3 API

- Neuer Router `src/football_betting/api/chat.py`, `POST /api/chat` (SSE), registriert in `api/app.py`.
- Rate-Limit via `slowapi` oder simples In-Memory-Token-Bucket
  (analog `scraping/rate_limiter`).
- Optionale Pydantic-Schemas in `api/schemas.py` ergänzen.

### 5.4 ENV-Variablen (Railway + lokal)

| Variable | Beispiel |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | `https://<resource>.openai.azure.com` |
| `AZURE_OPENAI_API_KEY` | `***` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | `gpt-4o-mini` |
| `AZURE_OPENAI_EMBED_DEPLOYMENT` | `text-embedding-3-small` |
| `LLM_MONTHLY_BUDGET_EUR` | `50` |
| `LLM_RATE_LIMIT_PER_HOUR` | `20` |

### 5.5 Frontend

- `web/components/SupportChat.tsx` erweitern:
  - FAQ-Fuzzy bei `score ≤ 0.2` weiterhin sofort antworten.
  - Sonst: SSE-Stream via `POST /api/chat`, Token-weise Rendering.
- Neuer Hook `web/lib/useChatStream.ts`.
- i18n-Keys ergänzen (`support.llm.disclaimer`, `support.llm.error`, `support.llm.thinking`)
  in `web/lib/i18n/{de,en,fr,es,it}.ts`.

### 5.6 Tests

- `tests/test_rag.py` — Index-Build, Retrieval-Quality (Recall@3 auf Gold-Query-Set).
- `tests/test_llm_chat.py` — Mock Azure-Responses, Tool-Calling-Flow, Locale-Routing.
- `tests/fixtures/llm_gold.jsonl` — 40 Gold-Q&A (8 pro Sprache).

### 5.7 Azure-Provisioning (separat, via azure-prepare)

- Azure OpenAI Resource + 2 Deployments (`gpt-4o-mini`, `text-embedding-3-small`).
- Key Vault für API-Key, Managed Identity Zugriff von Railway / Container Apps.
- Monthly-Budget-Alert bei 40 € und Hard-Stop bei 50 €.

## 6. Quality-Gate vor Merge

- LLM-as-a-Judge-Score ≥ **4 / 5** auf ≥ **90 %** der Gold-Samples.
- p95 Time-to-First-Token < **3 s**.
- Recall@3 des Retrievers ≥ **0,8** auf Gold-Query-Set.
- `ruff check .`, `mypy src`, `pytest` grün.

## 7. Offene Punkte / Risiken

- Azure OpenAI Region mit `gpt-4o-mini`-Verfügbarkeit prüfen (z. B. `swedencentral`, `eastus`).
- FAISS-Index-Persistenz: in Docker-Image einbacken vs. beim Container-Start bauen.
- Prompt-Injection-Schutz: Input-Sanitizer + System-Prompt-Hardening, optional Azure AI Content Safety.
- Cold-Start auf Railway: ggf. Modul-Lazy-Load, damit die FastAPI ohne LLM-Gebrauch nicht startet-blockiert.

## 8. Meilensteine

1. **M1** — Modul-Gerüst + `corpus.py` + `rag.py` + `fb rag-build` + Tests.
2. **M2** — `/api/chat`-Endpoint mit Streaming + Tool-Calling + Frontend-Integration.
3. **M3** — Azure-Provisioning + Quality-Gate + Release `v<next-minor>` + CHANGELOG.
