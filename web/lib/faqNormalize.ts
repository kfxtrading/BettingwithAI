/**
 * Input-robustness layer for the support-chat FAQ search.
 *
 * Handles four common user-input pathologies that Fuse.js alone cannot cover:
 *   1. Case / whitespace noise ("ValueBet", "  value   bet ")
 *   2. Missing or stray punctuation ("was ist btts")
 *   3. Diacritics / unicode variants ("Qué es una apuesta", "que es")
 *   4. Concatenated words ("valuebet", "bankrollmanagement", "closinglinevalue")
 *   5. Small typos (Levenshtein <= 2) against the tag vocabulary
 *
 * Pure, side-effect-free module — consumed by `faq.ts`.
 */

// ---------------------------------------------------------------------------
// 1) Character normalization
// ---------------------------------------------------------------------------

/**
 * Lowercase + NFKD-fold + strip combining marks + strip punctuation
 * (except intra-word hyphens) + collapse whitespace.
 * Keeps ASCII letters, digits and single spaces.
 */
export function normalizeText(raw: string): string {
  if (!raw) return '';
  // Replace German eszett + common ligatures that NFKD does not split cleanly.
  const preSubst = raw
    .replace(/ß/g, 'ss')
    .replace(/œ/gi, 'oe')
    .replace(/æ/gi, 'ae');
  const nfkd = preSubst.normalize('NFKD');
  // Strip combining diacritics (\u0300-\u036F).
  const noDiacritics = nfkd.replace(/[\u0300-\u036F]/g, '');
  // Lowercase then keep only [a-z0-9] and space; map everything else to space.
  const lowered = noDiacritics.toLowerCase();
  const cleaned = lowered.replace(/[^a-z0-9]+/g, ' ');
  return cleaned.replace(/\s+/g, ' ').trim();
}

/** Tokenize a normalized string. */
export function tokenize(normalized: string): string[] {
  if (!normalized) return [];
  return normalized.split(' ').filter(Boolean);
}

// ---------------------------------------------------------------------------
// 2) Concatenated-word splitter (vocab-driven DP segmentation)
// ---------------------------------------------------------------------------

const MIN_WORD_LEN = 2;
const MAX_SPLIT_TOKEN_LEN = 40;

/**
 * Greedy longest-match segmentation of a single token against a vocabulary.
 * Returns the input token unchanged if no full segmentation exists.
 *
 * Example (vocab has "value" and "bet"): "valuebet" -> "value bet".
 */
export function splitConcat(token: string, vocab: Set<string>): string {
  if (!token || token.length < 6 || token.length > MAX_SPLIT_TOKEN_LEN) return token;
  if (vocab.has(token)) return token;

  const n = token.length;
  // dp[i] = best segmentation of token.slice(0, i) as word-array, or null.
  const dp: (string[] | null)[] = Array.from({ length: n + 1 }, () => null);
  dp[0] = [];

  for (let i = 1; i <= n; i++) {
    // Prefer longer words (scan from long → short) for a more human-like split.
    for (let j = Math.max(0, i - 20); j < i; j++) {
      const slice = token.slice(j, i);
      if (slice.length < MIN_WORD_LEN) continue;
      if (!vocab.has(slice)) continue;
      const prev = dp[j];
      if (prev === null) continue;
      const candidate = [...prev, slice];
      const existing = dp[i];
      // Keep the segmentation with the fewest pieces (fewer = more likely correct).
      if (existing === null || candidate.length < existing.length) {
        dp[i] = candidate;
      }
    }
  }

  const seg = dp[n];
  if (seg && seg.length >= 2) return seg.join(' ');
  return token;
}

// ---------------------------------------------------------------------------
// 3) Typo correction (bounded Levenshtein against vocabulary)
// ---------------------------------------------------------------------------

/** Bounded Levenshtein distance. Returns `Infinity` once distance exceeds `max`. */
export function levenshteinBounded(a: string, b: string, max: number): number {
  if (a === b) return 0;
  const la = a.length;
  const lb = b.length;
  if (Math.abs(la - lb) > max) return Infinity;
  if (la === 0) return lb;
  if (lb === 0) return la;

  let prev = new Array(lb + 1);
  let cur = new Array(lb + 1);
  for (let j = 0; j <= lb; j++) prev[j] = j;

  for (let i = 1; i <= la; i++) {
    cur[0] = i;
    let rowMin = cur[0];
    for (let j = 1; j <= lb; j++) {
      const cost = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1;
      cur[j] = Math.min(
        prev[j] + 1,       // deletion
        cur[j - 1] + 1,    // insertion
        prev[j - 1] + cost // substitution
      );
      if (cur[j] < rowMin) rowMin = cur[j];
    }
    if (rowMin > max) return Infinity;
    [prev, cur] = [cur, prev];
  }
  return prev[lb];
}

/**
 * Find the closest vocabulary term to `token` within `max` edits.
 * Returns the token unchanged when no close candidate exists.
 * Short tokens (<4 chars) are never auto-corrected to avoid false positives.
 */
export function correctTypo(
  token: string,
  vocab: Set<string>,
  vocabList: string[],
  max = 2,
): string {
  if (token.length < 4) return token;
  if (vocab.has(token)) return token;
  let best = token;
  let bestDist = max + 1;
  for (const w of vocabList) {
    // Quick length gate — avoids calling Levenshtein on wildly different lengths.
    if (Math.abs(w.length - token.length) > max) continue;
    if (w.length < 4) continue;
    const d = levenshteinBounded(token, w, max);
    if (d < bestDist) {
      bestDist = d;
      best = w;
      if (d === 1) break; // 1-edit match is good enough
    }
  }
  return best;
}

// ---------------------------------------------------------------------------
// 4) Full query pipeline
// ---------------------------------------------------------------------------

/** Multi-language stop-words that must never become a split target. */
export const QUERY_STOPWORDS = new Set<string>([
  'a', 'an', 'the', 'is', 'it', 'of', 'to', 'in', 'on', 'for', 'and', 'or',
  'be', 'do', 'does', 'did', 'how', 'what', 'why', 'when', 'who', 'where',
  'ist', 'der', 'die', 'das', 'ein', 'eine', 'und', 'oder', 'mit', 'fuer', 'fur',
  'was', 'wie', 'wer', 'warum', 'wann', 'welche', 'welcher', 'welches', 'kann',
  'que', 'el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'es', 'son', 'como',
  'por', 'para', 'cual', 'cuales', 'cuando', 'donde', 'quien',
  'le', 'les', 'du', 'des', 'de', 'une', 'et', 'ou', 'quel', 'quelle', 'quoi',
  'comment', 'pourquoi', 'ce', 'ca',
  'il', 'lo', 'gli', 'uno', 'una', 'e', 'o', 'come', 'quale', 'quando',
  'perche', 'cosa', 'chi',
]);

export interface NormalizedQuery {
  /** Pure character-normalized form — keep for Fuse.js fuzzy pass. */
  readonly raw: string;
  /** Tokenized, concat-split, typo-corrected form — keep for tag matching. */
  readonly canonical: string;
  /** Individual canonical tokens. */
  readonly tokens: readonly string[];
}

/**
 * Run the full input-robustness pipeline on raw user input.
 *
 * Expands "ValueBet!" → `{ raw: "valuebet", canonical: "value bet", tokens: ["value","bet"] }`
 * when "value" and "bet" are both in the vocabulary.
 */
export function normalizeQuery(
  input: string,
  vocab: Set<string>,
  vocabList: string[],
): NormalizedQuery {
  const raw = normalizeText(input);
  if (!raw) return { raw: '', canonical: '', tokens: [] };

  const rawTokens = tokenize(raw);
  const expanded: string[] = [];

  for (const tok of rawTokens) {
    // 1) known word → keep
    if (vocab.has(tok)) {
      expanded.push(tok);
      continue;
    }
    // 2) try splitting concatenated compound
    const split = splitConcat(tok, vocab);
    if (split !== tok) {
      for (const w of split.split(' ')) expanded.push(w);
      continue;
    }
    // 3) try typo correction (skip stopwords to avoid nonsense corrections)
    if (!QUERY_STOPWORDS.has(tok)) {
      const corrected = correctTypo(tok, vocab, vocabList, 2);
      if (corrected !== tok) {
        expanded.push(corrected);
        continue;
      }
    }
    // 4) fall back to original token
    expanded.push(tok);
  }

  const canonical = expanded.join(' ').replace(/\s+/g, ' ').trim();
  return { raw, canonical, tokens: expanded };
}

// ---------------------------------------------------------------------------
// 5) Vocabulary builder
// ---------------------------------------------------------------------------

/**
 * Build a vocabulary Set from an arbitrary list of strings (tags, questions,
 * answers). Each string is normalized, tokenized and filtered by length.
 */
export function buildVocab(sources: readonly string[]): {
  vocab: Set<string>;
  vocabList: string[];
} {
  const vocab = new Set<string>();
  for (const s of sources) {
    const norm = normalizeText(s);
    for (const tok of tokenize(norm)) {
      if (tok.length >= 3 && !QUERY_STOPWORDS.has(tok)) vocab.add(tok);
      // also keep short common nouns like "xg", "ev"
      if (tok.length === 2 && /^[a-z]{2}$/.test(tok)) vocab.add(tok);
    }
  }
  return { vocab, vocabList: Array.from(vocab) };
}
