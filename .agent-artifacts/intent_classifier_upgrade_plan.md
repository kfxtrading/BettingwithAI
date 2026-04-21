# Support-Chatbot Intent-Classifier — Upgrade zu > 0.75 Top-1

Status: **Plan** · Owner: Marcel · Zielversion: nächster minor-Bump in `pyproject.toml` + CHANGELOG
Grundlage: externer Report "Optimierung der Intent-Klassifikation für deutschsprachige Support-Chatbots" (2026‑04‑21).

---

## 1. Ist-Zustand (gemessen)

- **268 Intents × 5 Sprachen** (en/de/es/fr/it), 9 Kapitel (general, basics, analysis, strategy, mistakes, ai, market, profit, platform) — siehe [./data/support_faq/stats.json](./data/support_faq/stats.json).
- **Augmentiertes Korpus**: 31.715 Zeilen, Ø **23,67 Paraphrasen/Intent** (min 13, max 41) — [./data/support_faq/augment_stats.json](./data/support_faq/augment_stats.json).
- **Top-1-Accuracy (val-Split)** aktuell laut [./models/support/benchmark_3way.json](./models/support/benchmark_3way.json):

| Lang | Fuse | ML (TF-IDF+LR) | Emb (e5-large) |
|---|---|---|---|
| en | 0.327 | 0.355 | 0.348 |
| de | 0.342 | 0.356 | 0.341 |
| es | 0.324 | 0.354 | 0.327 |
| fr | 0.282 | 0.314 | 0.287 |
| it | 0.292 | 0.330 | 0.305 |

- **Frontend**: [./web/components/SupportChat.tsx](./web/components/SupportChat.tsx) ruft rein clientseitig Fuse.js über [./web/lib/faq.ts](./web/lib/faq.ts); kein Zugriff auf das Python-ML-Backend.
- **Python-Backend**: `src/football_betting/support/` (IntentClassifier, EmbeddingIntentRetriever, IntentClusterer, CrossEncoderReranker) — vollständig vorhanden, aber **nicht online integriert** und erreicht das eigene Soft-Ziel `target_top1_accuracy=0.88` (siehe [./src/football_betting/config.py:410](./src/football_betting/config.py:410)) nicht.
- **Kein OOD-Intent, keine Hierarchie nach Kapitel, kein Noise-Augment während Fine-Tuning, keine Backtranslation, keine Supervised-Contrastive-Loss, keine API-Route.**

Gap zur Report-Empfehlung: (a) zu wenige Utterances/Intent, (b) 268 flache Klassen ohne Hierarchie, (c) keine Fehler-/Interpunktions-Resilienz im Training, (d) schwaches Backbone (TF-IDF bzw. Zero-Shot-e5), (e) keine Delta-Margin-Disambiguierung, (f) keine OOD-Klasse.

---

## 2. Zielbild

- **Top-1 ≥ 0.75** und **Top-3 ≥ 0.92** pro Sprache auf `dataset_augmented.jsonl`-val-Split.
- **Delta-Margin ≥ 0.15** zwischen Rang 1 und Rang 2 als Disambiguierungs-Gate.
- **OOD-Rejection F1 ≥ 0.7** auf einem neuen synthetischen OOD-Set.
- **p95 Latenz < 250 ms** serverseitig (CPU) für Top-1-Routing.
- Der Chat nutzt weiterhin Fuse.js als Sofort-Fallback (Offline-/Short-Circuit-Pfad), aber die primäre Antwort kommt vom Python-Classifier über eine neue FastAPI-Route.

---

## 3. Umsetzungsplan (sequenzielle Meilensteine)

### M1 — Hierarchische Taxonomie ("Pachinko", substantivbasiert)

Die 9 Kapitel (`chapter`) in [./data/support_faq/dataset.jsonl](./data/support_faq/dataset.jsonl) sind bereits substantivbasierte Oberthemen und werden zur Ebene-1-Klasse.

**Änderungen:**
1. Neuer Trainer-Pfad `train_hierarchical_one_language` in [./src/football_betting/support/trainer.py](./src/football_betting/support/trainer.py):
   - **Ebene 1 (Kapitel)**: ein TF-IDF+LR-Modell oder e5-basierter Klassifikator über 9 Klassen.
   - **Ebene 2 (Intent | Kapitel)**: pro Kapitel ein separater Head (lokaler Klassifikator pro Elternknoten), jeweils 20–40 Zielklassen statt 268.
2. Inferenz-Scoring: `P(intent) = P(kapitel) · P(intent | kapitel)` mit Backoff auf flache Verteilung, falls Ebene-1-Konfidenz < 0.4.
3. Persistenz: neues Filename-Template `support_hier_{lang}.joblib` (Dict: `topic_clf`, `leaf_clfs`, `chapter_labels`).
4. `IntentClusterer` ([./src/football_betting/support/cluster.py](./src/football_betting/support/cluster.py)) bleibt optional; Report bevorzugt klar **supervidierte Taxonomie** → Kapitel-Hierarchie ersetzt k-Means als primären Filter.
5. **OOD-Klasse `__ood__`** auf Ebene 1: ~500 LLM-synthetisierte themenfremde Sätze pro Sprache (Wetter, Urlaub, Rezepte, Arztanfragen) + 300 in-domain-aber-nicht-abgedeckte (ID-OOS) Beispiele.

### M2 — Dateneskalation auf ≥ 80 Utterances/Intent

**Ziel**: 268 × ~80 = **~21.500 Sätze/Sprache** (aktuell ~6.500 → Faktor ≈ 3,3).

**Vorgehen:**
1. Neues Script `scripts/augment_faq.py` mit drei Quellen, gesteuert per Flags:
   - **(a) LLM-Paraphrasierung** (bereits vorhanden in Ansatz, skalieren): pro Intent 60 neue Varianten via `gpt-4o-mini` (siehe Kosten-Kalkül in [./Erweiterungen/chatbot-llm-plan.md](./Erweiterungen/chatbot-llm-plan.md) — Budget < 2 €). Prompt erzwingt: Imperative, Fragen, Stichworte, Ellipsen, Längenvarianz.
   - **(b) Backtranslation-Pipeline**: Deutsch → {nl, fr, it} → Deutsch (analog für andere Sprachen) via `Helsinki-NLP/opus-mt-*` (sentence-transformers-kompatibel, offline). Report-Beleg: Rückübersetzung über Niederländisch signifikant (p<0.01) besser.
   - **(c) Noise-Injection** via `nlpaug`: `KeyboardAug(lang=<locale>)` (QWERTZ-Tippfehler), `RandomAug` (Satzzeichen & Kleinschreibung), aug_char_p=0.05, aug_word_p=0.1 auf 40 % des Korpus zusätzlich. Optional `OcrAug`.
2. Konsistenz-Enforcement im Augmenter: zentrale Liste von Füllwörtern ("Ich möchte", "Können Sie mir helfen", "Bitte") wird entweder in **allen Klassen** gleich verteilt oder konsequent entfernt (Report §2.2). Umsetzung: Post-Processing-Filter, der pro Intent die rel. Häufigkeit solcher Phrasen ausgleicht.
3. Klassenbalance: oversample seltene Intents auf mindestens 70 Utterances, falls LLM-Output lückenhaft.
4. Update von [./data/support_faq/augment_stats.json](./data/support_faq/augment_stats.json) + neuer Key `noise_profile`.
5. Neue Dependency-Gruppe `support-aug` in [./pyproject.toml](./pyproject.toml): `nlpaug`, `transformers`, `sentencepiece`, `sacremoses`, optional `openai`.

### M3 — Modell-Upgrade: ModernGBERT / XLM-RoBERTa-Fine-Tune + Contrastive Loss

**Begründung**: Report §4.3 → `ModernGBERT-134M` ist für Deutsch SOTA 2025; für EN/ES/FR/IT wird auf XLM-RoBERTa-Large (oder `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`) ausgewichen, um 5 Sprachen in einer Artefakt-Familie zu halten.

**Änderungen:**
1. Neues Modul `src/football_betting/support/transformer_model.py`:
   - Klasse `TransformerIntentClassifier` mit identischer Schnittstelle wie `IntentClassifier` (`fit`, `predict_topk`, `predict_proba_batch`, `save`/`load`).
   - Backbone konfigurierbar via `SupportConfig.transformer_model_name` (Default pro Sprache: `LSX-UniWue/ModernGBERT-134M` für de, `FacebookAI/xlm-roberta-base` sonst).
   - Training: HuggingFace `Trainer`, 3–5 Epochen, LR=2e-5 mit Linear-Warmup (10 %), Batch 16, Early Stopping auf val-macro-F1.
   - **Hybrid-Loss**: Cross-Entropy + `SupConLoss` (Gewicht 0.3) über Label-Aware-Pairs innerhalb jedes Batches. Implementierung direkt im `Trainer.compute_loss`-Override — Referenz: `https://github.com/HobbitLong/SupContrast`.
   - Speicherung: `support_transformer_{lang}/` als HF-Directory (tokenizer + model + id2label).
2. **Inferenz-Budget**: 134M-Modell läuft mit `onnxruntime`-Export (CPU-INT8) < 120 ms/Query. Export-Script unter `scripts/export_support_onnx.py`.
3. Hierarchie aus M1 wiederverwenden: Topic-Head kann auf dem gleichen Encoder als 2. Classification-Head (Multi-Task) sitzen (`total_loss = α·L_intent + β·L_topic + γ·L_supcon`).
4. Neue CLI-Subcommand-Gruppe in [./src/football_betting/cli.py](./src/football_betting/cli.py):
   - `fb support train-transformer --lang de|all`
   - `fb support export-onnx --lang all`
5. Benchmark-Script [./scripts/bench_support_intent.py](./scripts/bench_support_intent.py) erweitern um `--backend transformer` und `--backend hier-transformer`.

### M4 — Inferenz-Gateway + Frontend-Integration

1. Neuer Router `src/football_betting/api/support_chat.py`, registriert in `api/app.py`.
   - Endpoint `POST /api/support/intent` → Input `{text, lang}`, Output `{intent_id, score, top3: [...], needs_disambiguation: bool, fallback: bool}`.
   - Lädt Transformer-ONNX beim App-Startup lazy (cache in `api/services.py`).
   - Thresholding laut Report §6.2:
     - `score < 0.70` → `fallback=true` (Frontend zeigt FAQ-Hits + Free-Text-Fallback).
     - `score_top1 − score_top2 < 0.15` → `needs_disambiguation=true` (Frontend zeigt "Meinten Sie A oder B?"-Buttons mit den Top-3-Labels).
   - Rate-Limit 30 req/IP/min (reuse `scraping/rate_limiter`).
2. Frontend-Änderungen in [./web/components/SupportChat.tsx](./web/components/SupportChat.tsx):
   - Neuer Hook `web/lib/useIntentClassifier.ts`, ruft `/api/support/intent`.
   - Reihenfolge: **1.** Fuse.js Score ≤ 0.3 → Sofort-Antwort (offline-Pfad, keine Netzwerkkosten). **2.** Sonst API-Call. **3.** Bei `needs_disambiguation` → Chips mit Top-2. **4.** Bei `fallback` → bisherige Fallback-Kette (LLM/FAQ).
   - i18n-Keys `support.intent.disambiguation`, `support.intent.fallback` in allen 5 Locales.

### M5 — Evaluation, Monitoring, Human-in-the-Loop

1. **Gold-Set** `tests/fixtures/support_gold.jsonl`: 50 manuell kuratierte, realistisch verrauschte Nutzeranfragen pro Sprache (250 gesamt), inkl. 40 OOD-Beispielen.
2. **Erweiterte Metriken** in `IntentClassifier.evaluate` bzw. `TransformerIntentClassifier.evaluate`: Precision/Recall/F1 pro Intent, Confusion-Matrix, **ECE** (expected calibration error) post-Softmax, **AUROC OOD**. Dump nach `models/support/eval_report_{lang}.json`.
3. **Logging**: API loggt alle Queries mit `score`, `delta_margin`, `top3`, `selected_intent`, `user_accepted` (vom Frontend gemeldet) in `data/support_logs/YYYY-MM-DD.jsonl` → Rohmaterial für iterative Retrainings.
4. **CI-Quality-Gate** (pytest): neuer Test `tests/test_support_intent_accuracy.py`, der das gespeicherte Modell auf dem Gold-Set lädt und hart auf `top1 ≥ 0.75` pro Sprache prüft (skip, wenn Artefakt fehlt).
5. **Config-Gate**: `SUPPORT_CFG.min_top1_accuracy` von 0.75 belassen, `target_top1_accuracy` auf 0.85 absenken (realistisch), Warnung im Trainer bei Verfehlen.

---

## 4. Zu ändernde / neue Dateien (Überblick)

**Neu:**
- `src/football_betting/support/transformer_model.py`
- `src/football_betting/support/hierarchical.py`
- `src/football_betting/support/losses.py` (SupConLoss)
- `src/football_betting/support/augment.py` (nlpaug + backtranslate)
- `src/football_betting/api/support_chat.py`
- `scripts/augment_faq.py`
- `scripts/export_support_onnx.py`
- `web/lib/useIntentClassifier.ts`
- `tests/fixtures/support_gold.jsonl`
- `tests/test_support_intent_accuracy.py`
- `tests/test_support_hierarchical.py`
- `tests/test_support_augment.py`

**Anpassen:**
- [./src/football_betting/config.py](./src/football_betting/config.py) — neue Keys: `transformer_model_name`, `supcon_weight`, `noise_aug_profile`, `ood_label`, `delta_margin_threshold`, `confidence_threshold`.
- [./src/football_betting/support/trainer.py](./src/football_betting/support/trainer.py) — neue Funktionen `train_hierarchical_*`, `train_transformer_*`.
- [./src/football_betting/support/dataset.py](./src/football_betting/support/dataset.py) — Loader lernt OOD-Zeilen und Hierarchie-Labels.
- [./src/football_betting/support/__init__.py](./src/football_betting/support/__init__.py) — Re-Exporte.
- [./src/football_betting/cli.py](./src/football_betting/cli.py) — Subcommands `augment`, `train-hier`, `train-transformer`, `export-onnx`, `bench-all`.
- [./src/football_betting/api/app.py](./src/football_betting/api/app.py), [./src/football_betting/api/routes.py](./src/football_betting/api/routes.py), [./src/football_betting/api/schemas.py](./src/football_betting/api/schemas.py) — neuer Router.
- [./web/components/SupportChat.tsx](./web/components/SupportChat.tsx) — API-Call + Disambiguierung.
- [./web/lib/i18n/{de,en,fr,es,it}.ts](./web/lib) — neue Keys.
- [./pyproject.toml](./pyproject.toml) — Extras `support-aug`, `support-transformer` (transformers, torch, nlpaug, sentence-transformers, onnx, onnxruntime).
- [./CHANGELOG.md](./CHANGELOG.md).

---

## 5. Verifikation (End-to-End)

```bash
pip install -e ".[ml,dev,api,support-aug,support-transformer]"

# 1) Datenexpansion
fb support augment --lang all --target-per-intent 80 --noise-profile chat
python -c "import json; d=json.load(open('data/support_faq/augment_stats.json')); assert d['variants_per_intent_lang']['avg'] >= 75"

# 2) Hierarchie-Baseline (TF-IDF+LR)
fb support train-hier --lang all
# erwartet: per-language top1 ≥ 0.55 (Sanity-Zwischenschritt)

# 3) Transformer-Fine-Tune mit SupCon
fb support train-transformer --lang de   # ModernGBERT
fb support train-transformer --lang all  # XLM-R für restliche
# Harte Gate: models/support/eval_report_{lang}.json → top1_accuracy ≥ 0.75

# 4) Gold-Set-Bench
python scripts/bench_support_intent.py --backend hier-transformer --gold tests/fixtures/support_gold.jsonl
# alle 5 Sprachen müssen >= 0.75 Top-1 und >= 0.70 OOD-F1 liefern

# 5) ONNX-Export & API
fb support export-onnx --lang all
fb serve
curl -s -X POST http://localhost:8000/api/support/intent \
  -H "content-type: application/json" \
  -d '{"lang":"de","text":"wie resete ich mein paswort"}' \
  | jq '.intent_id, .score, .needs_disambiguation'
# erwartet: intent_id passend, score >= 0.7, needs_disambiguation=false

# 6) Frontend
cd web && npm run dev
# Manuell: typo-behaftete Eingaben in DE/EN/FR/ES/IT im Chat testen,
# Disambiguation-Chips müssen bei ambigen Queries erscheinen.

# 7) CI
pytest tests/test_support_intent_accuracy.py tests/test_support_hierarchical.py tests/test_support_augment.py -v
ruff check . && mypy src
```

**Abbruchkriterium**: Fällt top-1 auf dem Gold-Set in *einer* Sprache unter 0.70, wird M3 mit mehr SupCon-Gewicht / mehr Epochen wiederholt; fällt er in ≥ 2 Sprachen darunter, wird M2-Datenvolumen erhöht (Faktor 4 statt 3.3).
