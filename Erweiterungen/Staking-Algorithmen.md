# Staking-Algorithmen für 1X2-Fußballwetten im Realitätscheck

**Die ehrliche Antwort zuerst:** Reines konfidenzgewichtetes Staking ohne Quoten-Einbezug ist mathematisch strukturell unterlegen — es konzentriert Kapital systematisch auf Favoriten mit niedrigen Quoten und verschärft damit genau das Problem, das es lösen soll. Ein positives Gesamtergebnis bei exakt 50% Trefferquote ist nur dann möglich, wenn die **durchschnittliche Quote auf die Gewinner ≥ 2.00** beträgt — eine Hürde, die Max-Argmax-Picks aus 1X2-Modellen (typische Gewinnerquote 1.50–1.85) praktisch nie erreichen. Die akademische Literatur (Hubáček et al. 2019, Uhrín et al. 2021, Whitrow 2007) bietet für genau dieses Setting keine dominante Lösung; der **plausibelste Kompromiss** ist die sogenannte `conf`-Strategie `s_i = X · p_i / Σp_j` — aber nur, wenn sie mit einem **Odds-Dämpfungsfaktor** kombiniert wird. Im Folgenden eine systematische Analyse der neun angefragten Ansätze, ihre Formeln, die Break-even-Mathematik und eine praktische Python-Empfehlung mit realistischer Erwartungshaltung.

## Das Kernproblem: Konfidenz ohne Edge

Die neun vorgeschlagenen Ansätze lösen ein **Varianz-Problem**, nicht ein **Erwartungswert-Problem**. In einem effizienten 1X2-Markt mit ca. 5–8% Bookmaker-Marge gilt für kalibrierte Quoten `p_i · o_i ≈ 0.93–0.95` — also **jeder Pick hat denselben strukturell negativen EV**, unabhängig von der Modellkonfidenz. Jede Gewichtung, die nur `p_i` verwendet (ohne `o_i`), ändert daran nichts; sie verschiebt nur, wohin das Kapital fließt. Die Konsequenz ist mathematisch eindeutig:

**Gewichtung proportional zu `p_i` verlagert Kapital auf Favoriten mit niedriger Quote.** Das reduziert zwar die Tagesvarianz, senkt aber zugleich den erwarteten Bruttogewinn pro Euro Einsatz — weil `p_i·o_i` bei Favoriten typischerweise niedriger ist als bei Mid-Range-Picks. Whitrow (2007, *J. R. Stat. Soc. C*) und Uhrín et al. (2021, *IMA JMM*) zeigen formal: **Jede Allokationsstrategie, die unter Level-Stakes nicht profitabel ist, wird unter keinem Gewichtungsschema dauerhaft profitabel sein.** Pinnacle, Punter2Pro und Buchdahl (*Squares & Sharps*, 2016) formulieren denselben Satz als Kernmaxime der Quant-Betting-Praxis.

Die **Gleichung, die alles entscheidet**, lautet für eine erwartete Rendite > 0:
```
Σ_i w_i · p_i* · o_i  >  1         mit w_i = s_i/X und Σw_i = 1
```
wobei `p_i*` die *wahre* (nicht die Modell-) Wahrscheinlichkeit ist. **Nur wenn das Modell systematisch bessere `p_i*`-Schätzungen liefert als der Markt (Edge)**, kann diese Bedingung erfüllt werden — Staking-Gewichtung allein leistet das nicht.

## Die neun Ansätze im mathematischen Überblick

Die folgende Tabelle fasst alle angefragten Verfahren mit Python-kompatibler Formel und wissenschaftlicher Referenz zusammen. `X` = Tages-Bankroll, `p_i` = höchste 1X2-Modellwahrscheinlichkeit, `o_i` = zugehörige Dezimalquote, `σ_i² = p_i(1-p_i)·o_i²` = Per-Unit-Varianz der Einzelwette.

| # | Strategie | Formel (normalisiert auf X) | Quelle |
|---|-----------|----------------------------|--------|
| 1 | Flat / Equal (Baseline) | `s_i = X / N` | Dixon-Coles 1997; Constantinou 2013 |
| 2 | Proportional (conf) | `s_i = X · p_i / Σp_j` | Hubáček et al. 2019 ("conf") |
| 3 | Power-Law | `s_i = X · p_i^k / Σp_j^k`, k ∈ [1.5, 3] | implizit Whitrow 2007 |
| 4 | Softmax / Boltzmann | `s_i = X · exp(β·p_i) / Σexp(β·p_j)` | Sutton-Barto; Brill et al. 2024 |
| 5 | Threshold + Flat | `s_i = X/K` nur für p_i ≥ τ (K = # über τ) | Pinnacle; Pyckio |
| 6 | Tier/Rank-basiert | 3 Buckets (z.B. 50/30/20) oder `s_i ∝ (N+1-rank_i)` | Unit-System 1–10 (wettbasis, sportwettentest) |
| 7 | Entropie-gewichtet | `s_i = X · (1 - H_i/ln 3) / Σ(1 - H_j/ln 3)`, H_i = Shannon(P_full_i) | Brill/Wyner/Barnett 2024 |
| 8 | Inverse-Variance / Risk-Parity | `s_i = X · (1/σ_i²) / Σ(1/σ_j²)` | Palomar; Markowitz-Diagonal-Fall |
| 9 | Mean-Variance (QP) | max `μᵀs − (λ/2)sᵀΣs` s.t. 1ᵀs=X, s≥0 | Fitt 2009; Busseti/Ryu/Boyd 2016 |

**Softmax und Power-Law sind mathematisch äquivalent**: `exp(k·log p_i) / Σexp(k·log p_j) = p_i^k / Σp_j^k`. Das heißt: die Power-Transformation ist nichts anderes als Softmax auf Log-Wahrscheinlichkeiten mit Temperatur `1/k`. Die Entropie-Variante (Ansatz 7) ist **theoretisch überlegen gegenüber reiner `p_max`-Gewichtung**, weil sie die gesamte 3-Outcome-Verteilung nutzt — zwei Picks mit identischem `p_max = 0.55` können unterschiedliche Sicherheitsgrade haben (z.B. `(0.55, 0.40, 0.05)` vs. `(0.55, 0.25, 0.20)`), und nur die Entropie erfasst diesen Unterschied.

## Break-even-Mathematik: Die 2.00er Schwelle

Bei Flat-Staking mit `N` Tipps, Hitrate `h` und mittlerer Gewinnerquote `ō_w` gilt exakt:
```
ROI = h · ō_w − 1       ⟹   Break-even bei ō_w = 1/h
```
Das ergibt die **vier wichtigsten Schwellen** für die Praxis:

| Hitrate | Benötigte Ø-Gewinnquote |
|---------|-------------------------|
| 40% | 2.50 |
| 45% | 2.22 |
| **50%** | **2.00** |
| 55% | 1.82 |
| 60% | 1.67 |

**Das Problem bei 1X2-Argmax-Picks:** Ein Modell, das "den wahrscheinlichsten Ausgang" wählt, selektiert überwiegend Favoriten mit `p_max ∈ [0.55, 0.70]`, deren Marktquoten bei einem fair kalibrierten Buchmacher zwischen **1.40 und 1.80** liegen. Der erwartete Quotenschnitt solcher Picks liegt empirisch bei **1.70–1.85** — die Break-even-Hitrate ist damit nicht 50%, sondern **54–59%**. Bei exakt 50% Hitrate ergibt das einen erwarteten ROI von **−8% bis −12%**.

**Die Rettung kommt nicht vom Staking, sondern von der Pick-Zusammensetzung**: Wenn das Modell regelmäßig auch Mid-Range-Picks (p_max ≈ 0.40–0.50 bei Quoten 2.00–2.50) und gelegentliche X-Picks (p_max ≈ 0.33 bei Quoten 3.00–3.50) ausgibt, steigt der durchschnittliche Gewinnerquoten-Mix auf > 2.00 und 50% Hitrate kann tatsächlich profitabel sein. Das ist **keine Frage der Gewichtung, sondern der Modell-Auswahl**.

## Der Paradox-Effekt gewichteter Allokation

Ein konkretes Zahlenbeispiel macht das Paradox sichtbar. 14 Tipps, Bankroll X = 1000 €, drei Konfidenz-Tiers:

- 5 High-Picks (p ≈ 0.65, o ≈ 1.55)
- 5 Mid-Picks (p ≈ 0.50, o ≈ 2.00)  
- 4 Low-Picks (p ≈ 0.40, o ≈ 2.70)

Bei `conf`-Staking erhalten High-Picks je ~103 €, Mid-Picks je ~69 €, Low-Picks je ~35 €. Der **erwartete Gesamtgewinn** (bei korrekt kalibriertem Modell) beträgt:

```
E[ROI] = 5·103·(0.65·1.55−1) + 5·69·(0.50·2.00−1) + 4·35·(0.40·2.70−1)
       = +3.88 + 0 + +11.04  ≈  +15 €  (+1.5%)
```

**Der positive Erwartungswert kommt fast ausschließlich aus den Low-Picks** — und die bekommen das geringste Gewicht. Eine **flat** Verteilung würde in diesem Szenario +25 € (+2.5%) EV liefern, also **fast doppelt so viel** wie conf-Staking. Das ist kein Rechentrick, sondern strukturell: Je stärker man nach `p` konzentriert, desto mehr Kapital landet bei den Picks mit dem schwächsten EV pro Euro.

## Konzentration messen: HHI und effektive Tipp-Anzahl

Für jede Strategie lässt sich die tatsächliche Konzentration über den Herfindahl-Hirschman-Index `HHI = Σw_i²` und die **effektive Anzahl Tipps** `N_eff = 1/HHI` quantifizieren. Für N = 14 Picks gilt: Flat → N_eff = 14, conf → N_eff ≈ 12–13, Power k=2 → N_eff ≈ 10, Softmax β=5 → N_eff ≈ 7, Winner-takes-all → N_eff = 1. Die **empirisch robuste Zielzone bei kalibrierten Wahrscheinlichkeiten mit p_max ≤ 0.70** liegt bei `N_eff ∈ [8, 11]` — starke Konzentration ist statistisch nicht gerechtfertigt, da die Spreizung der p-Werte gering ist.

## Was die Literatur explizit empfiehlt

**Hubáček, Šourek, Železný (2019)** testen in *International Journal of Forecasting* fünf Strategien auf NBA-Daten: unif (Flat), conf (proportional zu p̂), abs-disc, rel-disc und opt (Mean-Variance/Sharpe-max). Ergebnis: **unif und conf sind verlustig (-0.4% bis -5.5%), opt ist profitabel (+0.9% bis +1.7%)** — aber `opt` nutzt Odds als Input. Uhrín et al. (2021, *IMA JMM*) bestätigen: **adaptives Fractional Kelly** ist die robusteste Strategie über Soccer, Basketball und Pferderennen — aber setzt einen geschätzten Edge voraus. **Whitrow (2007)** zeigt analytisch: Bei vielen simultanen Wetten konvergiert die optimale Allokation näherungsweise gegen proportional-zu-Einzel-Kelly.

Keine peer-reviewed Publikation empfiehlt reines konfidenzgewichtetes Staking ohne Edge-Einbezug. Buchdahl (2016), Pinnacle Betting Resources und Punter2Pro formulieren übereinstimmend: *"Any selection method that doesn't profit at level stakes won't succeed under any staking plan."* Die deutsche Szene (wettbasis, sportwettentest) nutzt das **1–10-Unit-System** als Tier-Heuristik, koppelt die Unit-Wahl aber in der Praxis an Edge, nicht an reine Konfidenz.

## Konkrete Python-Empfehlung: Der Hybrid-Ansatz

Wenn die Anforderung "gewichtet nach Modellkonfidenz, feste Bankroll, keine Edge-Berechnung" politisch gesetzt ist, bleibt als mathematisch vertretbarer Kompromiss eine **conf-Variante mit Odds-Dämpfung** — sie respektiert die Konfidenz-Priorität, verhindert aber die pathologische Überallokation auf Niedrigquoten-Favoriten:

```python
import numpy as np

def hybrid_stakes(X, p, o, k=2.0, odds_floor=2.0, min_p=0.40):
    """
    X:          Tages-Bankroll
    p:          array of p_max (confidence der Argmax-Picks)
    o:          array of Dezimalquoten der Argmax-Picks
    k:          Konzentrations-Exponent (1=linear prop, 2=moderat konzentriert)
    odds_floor: Quoten-Referenz; Picks mit o < floor werden gedämpft
    min_p:      Threshold unter dem Picks ausgeschlossen werden
    """
    p = np.asarray(p, dtype=float)
    o = np.asarray(o, dtype=float)
    mask = p >= min_p
    # Konfidenz-Komponente (Power-Law)
    conf_w = np.where(mask, p**k, 0.0)
    # Odds-Dämpfung: Favoriten mit o < 2.0 werden abgeschwächt
    odds_factor = np.minimum(o / odds_floor, 1.0)
    w = conf_w * odds_factor
    if w.sum() == 0:
        return np.zeros_like(p)
    return X * w / w.sum()

def diag(stakes):
    w = stakes / stakes.sum()
    hhi = (w**2).sum()
    return {"HHI": hhi, "N_eff": 1/hhi, "max_weight": w.max()}
```

Empfohlene Parameter für N ≈ 14, p_max ∈ [0.40, 0.70]: `k = 2.0`, `odds_floor = 2.0`, `min_p = 0.40`. Das ergibt typisch `N_eff ≈ 9–11` und verhindert, dass mehr als ~15% der Bankroll auf einen einzelnen Pick gehen.

**Als theoretisch sauberere Alternative** (nutzt volle 3-Outcome-Verteilung) die Entropie-Variante:

```python
def entropy_stakes(X, P_full, eps=1e-12):
    """P_full: (N, 3)-array mit (p_H, p_X, p_A) je Spiel"""
    H = -np.sum(P_full * np.log(P_full + eps), axis=1)
    conf = 1 - H / np.log(3)
    return X * conf / conf.sum()
```

## Realistische Erwartungshaltung und klare Empfehlung

**Die ehrliche Antwort auf die Frage, ob 50% Trefferquote positive Rendite liefern kann:** Ja — aber nur unter einer von zwei Bedingungen. Entweder selektiert das Modell regelmäßig Picks mit **ø-Gewinnerquote ≥ 2.00** (was bei reinem Argmax-Selection-Regime statistisch selten ist, da Argmax Favoriten bevorzugt). Oder das Modell hat einen echten **Edge gegenüber dem Bookmaker-Closing** — dann aber wäre klassisches Fractional Kelly (25–50%) mit Edge-Filter die mathematisch korrekte Antwort, nicht ein Konfidenzschema.

**Für den beschriebenen Use Case (CatBoost + pi-ratings, 14 Tipps/Tag, Argmax-Selection, keine Value-Logik)** ist die pragmatische Empfehlung zweiteilig: Erstens, den obigen **Hybrid-Algorithmus** (Power-k=2 mit Odds-Dämpfung) als Produktivlösung implementieren, weil er die Konfidenz-Anforderung erfüllt und das Favoriten-Traps-Problem abmildert. Zweitens, **parallel ein Flat-Staking-Backtest** als Benchmark mitlaufen lassen — wenn das System unter Flat nicht profitabel ist, wird es unter keiner Gewichtung profitabel. Als Zielmetrik für die Konzentration dient `N_eff ∈ [8, 11]` bei N = 14.

Die einzige Strategie, die in kontrollierten akademischen Backtests (Hubáček 2019, Uhrín 2021) konsistent positive Renditen erzeugte, ist die **Mean-Variance-Optimierung mit Sharpe-Ratio-Maximierung** (Ansatz 9) — sie benötigt die Odds als Input und ist in zehn Zeilen CVXPY implementierbar. Wenn die strikte "keine Quoten"-Beschränkung aufgeweicht werden kann, ist das die wissenschaftlich fundierteste Wahl.

## Zentrale Erkenntnisse zum Mitnehmen

Die Recherche verdichtet sich auf drei harte mathematische Befunde, die jeder 1X2-Quant akzeptieren muss. **Erstens:** Die Break-even-Hitrate ist nicht 50%, sondern `1/ø_Gewinnerquote` — bei typischen Argmax-Picks im Fußball also eher 54–58%. **Zweitens:** Reine p-Gewichtung verschiebt Kapital in EV-ungünstige Regionen; sie ist der Flat-Strategie nicht nur theoretisch, sondern in den wenigen verfügbaren Backtests auch empirisch unterlegen. **Drittens:** Jede ernsthafte Lösung nutzt entweder Odds (Mean-Variance, Kelly, unit-impact) oder die volle 3-Outcome-Entropie — nicht nur `p_max`. Ein konfidenzgewichteter Staking-Plan kann die Varianz glätten und das psychologische Nutzererlebnis verbessern, aber er ist kein Werkzeug, um aus einem strukturell negativ-EV-Selection-Regime ein profitables System zu machen. Wer das Ziel "positives Ergebnis bei 50% Hitrate" ernst nimmt, muss beim **Modell und der Pick-Auswahl** ansetzen — nicht beim Stake-Allokator.