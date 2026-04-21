# Plan: ML Training for Support Chatbot (Intent Classifier)

## Goal
Train a lightweight, per-language intent-classification model on
`data/support_faq/dataset_augmented.jsonl` (30,815 rows · 268 intents · 5 langs)
so the Support chatbot can map free-form user questions to the correct FAQ
intent far more robustly than today's Fuse.js fuzzy search.

This is the **local ML baseline** that precedes the Azure-OpenAI + RAG path in
`Erweiterungen/chatbot-llm-plan.md`. It ships the ML artefact + offline eval
only — frontend wiring and a `/api/support/classify` endpoint are follow-ups.

## Approach (recommended)

**TF-IDF (char_wb 3–5  ⊕  word 1–2) → Logistic Regression**, trained **once per
locale** (`en`, `de`, `es`, `fr`, `it`). Persisted via `joblib`.

Why:
- `scikit-learn` is already a core dep (`pyproject.toml` L16) — **zero new deps**.
- 268 intents × ~23 variants/lang is a textbook small-scale multiclass task.
  TF-IDF + LR routinely hits top-1 ≥ 0.9 / top-3 ≥ 0.98 on such sets.
- Character n-grams handle morphology + typos in DE/ES/FR/IT without a
  multilingual embedding model.
- One model per language keeps each classifier small, locale-routed, and
  consistent with the i18n-per-file frontend layout.
- Mirrors the project’s existing `fit/predict/save/load` class pattern
  (see `src/football_betting/predict/mlp_model.py`).

Alternatives considered & rejected for this iteration:
- `sentence-transformers` embeddings → heavy dep, runtime inference cost,
  unnecessary for a closed-set 268-intent task.
- `fastText` → extra native dep, marginal gains over sklearn TF-IDF+LR.
- Fine-tuning the existing PyTorch MLP → overkill for sparse text features;
  adds training time with no accuracy advantage.
- Single multilingual model → muddies class boundaries & makes per-locale
  thresholds harder to tune; no UX benefit since UI locale is known.

## Files to Create / Edit

### New (implementation)
| File | Purpose |
|---|---|
| `src/football_betting/support/__init__.py` | Package marker + public exports |
| `src/football_betting/support/text.py` | `normalize(text)` — NFC, lowercase, whitespace collapse, strip accents (optional toggle) |
| `src/football_betting/support/dataset.py` | `load_dataset(path, lang) -> (X, y, meta)`; stratified train/val split helpers |
| `src/football_betting/support/intent_model.py` | `IntentClassifier` with `fit / predict / predict_topk / save / load`. sklearn `Pipeline`: `FeatureUnion(char_wb 3-5, word 1-2)` → `LogisticRegression(C=4.0, class_weight='balanced', max_iter=2000, n_jobs=-1)` |
| `scripts/train_support.py` | Thin wrapper: iterates locales, trains, writes artefacts + `models/support_intent_metrics.json` |

### New (tests)
| File | Purpose |
|---|---|
| `tests/test_support_intent.py` | ~8 tests: dataset loader shape & lang filter, fit on tiny subset, top-k ordering + sum, save/load round-trip, unknown-locale raises, normalizer idempotence, metrics file schema |

### Edit
| File | Change |
|---|---|
| `src/football_betting/config.py` | Add `SUPPORT_CFG` dataclass + constants (`SUPPORT_DATA_DIR`, `SUPPORT_MODELS_DIR = MODELS_DIR / "support"`, default thresholds, hyperparams). Keep existing style |
| `src/football_betting/cli.py` | Register `fb train-support` Click subcommand (`--lang all|en|de|es|fr|it`, `--dataset`, `--out-dir`). Must follow kebab-case convention per `AGENTS.md` |
| `CHANGELOG.md` | New unreleased entry: "support: TF-IDF + LR intent classifier, per-locale" |
| `pyproject.toml` | Bump version to `0.3.1` (patch) in lockstep with the CHANGELOG entry |

No frontend changes. No new runtime deps.

## Data Contract

Input rows (already present in `data/support_faq/dataset_augmented.jsonl`):
```json
{"id": "value-bet", "lang": "en", "chapter": "general",
 "question": "Where is the edge on this one?", "answer": "...",
 "tags": [...], "variant": 3, "source": "paraphrase"}
```

Trained label = `id` (the intent ID, 268 classes). `answer` + `tags` are
**not** used as training inputs (answer is the downstream lookup target;
tags caused label leakage when spot-tested).

## Training Configuration (defaults in `SUPPORT_CFG`)

```
vectorizer = FeatureUnion([
    ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                             min_df=2, sublinear_tf=True)),
    ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2),
                             min_df=2, sublinear_tf=True,
                             token_pattern=r"(?u)\b\w+\b")),
])
classifier = LogisticRegression(
    C=4.0, class_weight="balanced", max_iter=2000,
    solver="liblinear",       # good for sparse, multinomial via OvR
    n_jobs=None, random_state=42,
)
```
Stratified split: 85 % train / 15 % val, `random_state=42`. `original` rows
always placed in train to avoid unseen intents in val.

## Artefacts

```
models/support/
  support_intent_en.joblib
  support_intent_de.joblib
  support_intent_es.joblib
  support_intent_fr.joblib
  support_intent_it.joblib
  support_intent_metrics.json   # per-lang top1/top3/macro-F1 + per-chapter acc
```

`support_intent_metrics.json` acceptance gate (soft, log-warn only):
- top-1 ≥ 0.88, top-3 ≥ 0.97, macro-F1 ≥ 0.85 per language.
- These are realistic for 23 avg variants/intent; fail-loud if any lang <0.75.

## Inference API (Python-only for this PR)

```python
clf = IntentClassifier.load(MODELS_DIR / "support" / "support_intent_en.joblib")
top = clf.predict_topk("what is a value bet?", k=3)
# [("value-bet", 0.91), ("kelly", 0.03), ("edge", 0.02)]
```

Applying this to FastAPI / frontend is explicitly **out of scope** here and
tracked as a follow-up (a new `/api/support/classify` route + SSE + frontend
fallback chain: exact tag match → TF-IDF-LR → Fuse → fallback text).

## Verification (end-to-end)

```bash
# 1. Lint + type-check
ruff check .
mypy src

# 2. Unit tests (fast)
pytest tests/test_support_intent.py -v

# 3. Full training run (~30–90 s on CPU for all 5 langs)
fb train-support --lang all

# 4. Inspect metrics
type models\support\support_intent_metrics.json

# 5. Smoke predictions (quick Python REPL)
python -c "from football_betting.support.intent_model import IntentClassifier; \
           from football_betting.config import MODELS_DIR; \
           m = IntentClassifier.load(MODELS_DIR / 'support' / 'support_intent_en.joblib'); \
           print(m.predict_topk('how are odds calculated?', k=3))"

# 6. Whole repo regression
pytest
```

## Out of Scope (explicit follow-ups)
- `POST /api/support/classify` FastAPI route + Pydantic schema.
- Frontend wiring in `web/components/SupportChat.tsx` (chained fallback).
- `skl2onnx` export for edge inference.
- Active-learning loop from real user queries.
- Anything from `Erweiterungen/chatbot-llm-plan.md` (Azure OpenAI + RAG).

## Critical Files Referenced
- Data: [./data/support_faq/dataset_augmented.jsonl](./data/support_faq/dataset_augmented.jsonl) · [./data/support_faq/stats.json](./data/support_faq/stats.json) · [./data/support_faq/augment_stats.json](./data/support_faq/augment_stats.json) · [./data/support_faq/intents.json](./data/support_faq/intents.json)
- Pattern reference: [./src/football_betting/predict/mlp_model.py](./src/football_betting/predict/mlp_model.py) · [./src/football_betting/predict/catboost_model.py](./src/football_betting/predict/catboost_model.py)
- Prep scripts: [./scripts/export_support_faq.py](./scripts/export_support_faq.py) · [./scripts/augment_support_faq.py](./scripts/augment_support_faq.py)
- CLI: [./src/football_betting/cli.py](./src/football_betting/cli.py)
- Config: [./src/football_betting/config.py](./src/football_betting/config.py)
- Frontend (current Fuse baseline): [./web/components/SupportChat.tsx](./web/components/SupportChat.tsx) · [./web/lib/faq.ts](./web/lib/faq.ts)
