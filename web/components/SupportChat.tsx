'use client';

import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowLeft, ExternalLink, MessageCircle, Send, TrendingUp, X } from 'lucide-react';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import {
  FAQ_ENTRIES,
  buildFuse,
  searchFaq,
  type FaqEntry,
} from '@/lib/faq';
import { api, type MatchContext } from '@/lib/api';

type Message =
  | { role: 'user'; text: string }
  | { role: 'bot'; text: string; followUpEntryId?: string; matchContext?: MatchContext };

const SUGGESTION_LIMIT = 5;

function FormBadge({ form }: { form: string }) {
  return (
    <span className="font-mono text-xs tracking-widest">
      {form.split('').map((c, i) => (
        <span
          key={i}
          className={
            c === 'W'
              ? 'text-emerald-500'
              : c === 'D'
                ? 'text-amber-500'
                : 'text-red-500'
          }
        >
          {c}
        </span>
      ))}
    </span>
  );
}

function MatchContextCard({ ctx, t }: { ctx: MatchContext; t: (k: string) => string }) {
  const labels: Record<'H' | 'D' | 'A', string> = { H: ctx.home_team, D: 'Draw', A: ctx.away_team };
  const pct = (v: number) => `${Math.round(v * 100)}%`;
  const bars: { label: string; value: number; colour: string }[] = [
    { label: ctx.home_team, value: ctx.prob_home, colour: 'bg-blue-500' },
    { label: 'Draw', value: ctx.prob_draw, colour: 'bg-slate-400' },
    { label: ctx.away_team, value: ctx.prob_away, colour: 'bg-violet-500' },
  ];

  return (
    <div className="mr-auto w-full max-w-[90%] overflow-hidden rounded-[10px] border border-border bg-surface-2 text-xs text-text">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2">
        <span className="font-semibold">
          {ctx.home_team} <span className="text-muted">vs</span> {ctx.away_team}
        </span>
        {ctx.value_bet && (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-2xs font-semibold text-emerald-600 dark:text-emerald-400">
            <TrendingUp size={10} aria-hidden="true" />
            {t('support.match.valueBet')}
          </span>
        )}
      </div>

      <div className="space-y-2 px-3 py-2">
        {/* League + kickoff */}
        <div className="flex items-center gap-3 text-2xs text-muted">
          <span>{ctx.league_name}</span>
          {ctx.kickoff_time && (
            <>
              <span aria-hidden="true">·</span>
              <span>
                {t('support.match.kickoff')}: {ctx.kickoff_time}
              </span>
            </>
          )}
        </div>

        {/* Probability bars */}
        <div>
          <p className="mb-1 text-2xs font-medium uppercase tracking-[0.1em] text-muted">
            {t('support.match.probs')}
          </p>
          <div className="space-y-1">
            {bars.map((b) => (
              <div key={b.label} className="flex items-center gap-2">
                <span className="w-[72px] truncate text-right text-2xs text-muted">
                  {b.label}
                </span>
                <div className="flex-1 overflow-hidden rounded-full bg-surface h-1.5">
                  <div
                    className={`h-full rounded-full ${b.colour} ${b.label === labels[ctx.most_likely] ? 'opacity-100' : 'opacity-40'}`}
                    style={{ width: pct(b.value) }}
                  />
                </div>
                <span className={`w-8 text-right text-2xs ${b.label === labels[ctx.most_likely] ? 'font-semibold text-text' : 'text-muted'}`}>
                  {pct(b.value)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Form */}
        {(ctx.form_home || ctx.form_away) && (
          <div>
            <p className="mb-1 text-2xs font-medium uppercase tracking-[0.1em] text-muted">
              {t('support.match.form')}
            </p>
            <div className="flex gap-4">
              {ctx.form_home && (
                <div className="flex items-center gap-1.5">
                  <span className="text-2xs text-muted">{ctx.home_team.split(' ')[0]}</span>
                  <FormBadge form={ctx.form_home} />
                </div>
              )}
              {ctx.form_away && (
                <div className="flex items-center gap-1.5">
                  <span className="text-2xs text-muted">{ctx.away_team.split(' ')[0]}</span>
                  <FormBadge form={ctx.form_away} />
                </div>
              )}
            </div>
          </div>
        )}

        {/* News */}
        {ctx.news.length > 0 && (
          <div>
            <p className="mb-1 text-2xs font-medium uppercase tracking-[0.1em] text-muted">
              {t('support.match.news')}
            </p>
            <ul className="space-y-1">
              {ctx.news.map((item, i) => (
                <li key={i} className="flex items-start gap-1">
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex min-w-0 items-center gap-1 text-2xs text-accent hover:underline"
                  >
                    <ExternalLink size={10} className="flex-none" aria-hidden="true" />
                    <span className="truncate">{item.title}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
const MATCH_SCORE_THRESHOLD = 0.6;
const FOLLOW_UP_CONFIDENCE_THRESHOLD = 0.4;
// Transformer score gate — below this we still try the Fuse.js fallback so
// the user never gets a dead-end answer when the top-1 intent is borderline.
const TRANSFORMER_MIN_SCORE = 0.35;

export function SupportChat() {
  const { t, locale } = useLocale();
  const panelId = useId();

  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);

  const fuse = useMemo(() => buildFuse(t), [t]);

  const suggestions = useMemo<FaqEntry[]>(
    () => FAQ_ENTRIES.slice(0, SUGGESTION_LIMIT),
    [],
  );

  const byId = useMemo(
    () => new Map(FAQ_ENTRIES.map((e) => [e.id, e] as const)),
    [],
  );

  const handleAsk = useCallback(
    (question: string) => {
      const text = question.trim();
      if (!text) return;

      // Optimistically push the user message, then resolve the answer.
      setMessages((prev) => [...prev, { role: 'user', text }]);
      setInput('');

      const fuseFallback = (): {
        answer: string;
        followUpEntryId: string | undefined;
      } => {
        const matches = searchFaq(text, fuse);
        const top = matches[0];
        const hit =
          top && top.score <= MATCH_SCORE_THRESHOLD ? top : undefined;
        const answer = hit ? t(hit.entry.answerKey) : t('support.fallback');
        const followUpEntryId =
          hit &&
          hit.score <= FOLLOW_UP_CONFIDENCE_THRESHOLD &&
          hit.entry.followUpId &&
          byId.has(hit.entry.followUpId)
            ? hit.entry.followUpId
            : undefined;
        return { answer, followUpEntryId };
      };

      const resolveFromPrediction = (
        intentId: string,
      ): { answer: string; followUpEntryId: string | undefined } | null => {
        const entry = byId.get(intentId);
        if (!entry) return null;
        return {
          answer: t(entry.answerKey),
          followUpEntryId:
            entry.followUpId && byId.has(entry.followUpId)
              ? entry.followUpId
              : undefined,
        };
      };

      const appendBot = (
        answer: string,
        followUpEntryId?: string,
        matchContext?: MatchContext,
      ) => {
        setMessages((prev) => [
          ...prev,
          { role: 'bot', text: answer, followUpEntryId, matchContext },
        ]);
      };

      void api
        .supportAsk({ question: text, lang: locale, top_k: 3 })
        .then((res) => {
          const ctx = res.match_context ?? undefined;
          const top = res.predictions[0];
          if (!res.fallback && top && top.score >= TRANSFORMER_MIN_SCORE) {
            const resolved = resolveFromPrediction(top.intent_id);
            if (resolved) {
              appendBot(resolved.answer, resolved.followUpEntryId, ctx);
              return;
            }
          }
          const fb = fuseFallback();
          appendBot(fb.answer, fb.followUpEntryId, ctx);
        })
        .catch(() => {
          const fb = fuseFallback();
          appendBot(fb.answer, fb.followUpEntryId);
        });
    },
    [byId, fuse, locale, t],
  );

  const lastBot = [...messages].reverse().find((m) => m.role === 'bot') as
    | Extract<Message, { role: 'bot' }>
    | undefined;
  const lastBotIdx = lastBot ? messages.lastIndexOf(lastBot) : -1;
  const followUpEntry =
    lastBot?.followUpEntryId ? byId.get(lastBot.followUpEntryId) : undefined;
  const followUpConsumed =
    lastBotIdx >= 0 && followUpEntry
      ? messages
          .slice(lastBotIdx + 1)
          .some(
            (m) =>
              m.role === 'user' &&
              m.text.trim() === t(followUpEntry.questionKey).trim(),
          )
      : false;

  useEffect(() => {
    if (open) {
      const id = window.setTimeout(() => inputRef.current?.focus(), 120);
      return () => window.clearTimeout(id);
    }
    return undefined;
  }, [open]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setOpen(false);
        toggleRef.current?.focus();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-40 flex flex-col items-end gap-2">
      <AnimatePresence>
        {open && (
          <motion.div
            id={panelId}
            role="dialog"
            aria-modal="false"
            aria-label={t('support.panel.title')}
            initial={{ opacity: 0, y: 12, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.97 }}
            transition={{ duration: 0.18, ease: [0.25, 0.1, 0.25, 1] }}
            className="pointer-events-auto flex h-[480px] w-[min(360px,calc(100vw-2rem))] flex-col overflow-hidden rounded-[14px] border border-border bg-surface shadow-soft"
          >
            <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
              <div className="flex min-w-0 items-center gap-2">
                {messages.length > 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      setMessages([]);
                      setInput('');
                      inputRef.current?.focus();
                    }}
                    aria-label={t('support.reset')}
                    className="focus-ring press inline-flex items-center gap-1 rounded-full border border-border bg-surface-2 px-2 py-1 text-2xs font-medium text-muted hover:border-accent hover:text-text"
                  >
                    <ArrowLeft size={12} aria-hidden="true" />
                    {t('support.reset')}
                  </button>
                )}
                <span className="truncate text-sm font-medium text-text">
                  {t('support.panel.title')}
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  toggleRef.current?.focus();
                }}
                aria-label={t('support.panel.close')}
                className="focus-ring press flex-none rounded-full p-1 text-muted hover:text-text"
              >
                <X size={16} />
              </button>
            </div>

            <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4 text-sm">
              {messages.length === 0 ? (
                <div className="space-y-2">
                  <p className="text-2xs font-medium uppercase tracking-[0.12em] text-muted">
                    {t('support.suggestions.heading')}
                  </p>
                  <div className="flex flex-col gap-2">
                    {suggestions.map((entry) => (
                      <button
                        key={entry.id}
                        type="button"
                        onClick={() => handleAsk(t(entry.questionKey))}
                        className="focus-ring press rounded-[10px] border border-border bg-surface-2 px-3 py-2 text-left text-sm text-text transition-colors hover:border-accent"
                      >
                        {t(entry.questionKey)}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {messages.map((msg, i) => (
                    <div key={i} className="flex flex-col gap-1.5">
                      {msg.role === 'bot' && msg.matchContext && (
                        <MatchContextCard ctx={msg.matchContext} t={t} />
                      )}
                      <div
                        className={
                          msg.role === 'user'
                            ? 'ml-auto max-w-[85%] rounded-[10px] bg-accent px-3 py-2 text-sm text-white'
                            : 'mr-auto max-w-[90%] rounded-[10px] bg-surface-2 px-3 py-2 text-sm text-text'
                        }
                      >
                        {msg.text}
                      </div>
                    </div>
                  ))}
                  {followUpEntry && !followUpConsumed && (
                    <button
                      type="button"
                      onClick={() => handleAsk(t(followUpEntry.questionKey))}
                      className="focus-ring press mr-auto max-w-[90%] rounded-[10px] border border-border bg-surface-2 px-3 py-2 text-left text-sm text-text transition-colors hover:border-accent"
                    >
                      {'\u21B3 '}
                      {t(followUpEntry.questionKey)}
                    </button>
                  )}
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAsk(input);
              }}
              className="flex items-center gap-2 border-t border-border px-3 py-3"
            >
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={t('support.input.placeholder')}
                className="focus-ring flex-1 rounded-[10px] border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-muted"
              />
              <button
                type="submit"
                aria-label={t('support.input.send')}
                disabled={!input.trim()}
                className="focus-ring press inline-flex h-9 w-9 flex-none items-center justify-center rounded-full bg-accent text-white disabled:opacity-50"
              >
                <Send size={15} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      <button
        ref={toggleRef}
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={panelId}
        className="focus-ring press pointer-events-auto inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-2.5 text-sm font-medium text-text shadow-soft transition-colors hover:border-accent"
      >
        <MessageCircle size={16} className="text-accent" aria-hidden="true" />
        {t('support.toggle.label')}
      </button>
    </div>
  );
}
