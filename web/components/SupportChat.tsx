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
import { MessageCircle, Send, X } from 'lucide-react';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import {
  FAQ_ENTRIES,
  buildFuse,
  searchFaq,
  type FaqEntry,
} from '@/lib/faq';

type Message =
  | { role: 'user'; text: string }
  | { role: 'bot'; text: string };

const SUGGESTION_LIMIT = 5;
const MATCH_SCORE_THRESHOLD = 0.6;

export function SupportChat() {
  const { t } = useLocale();
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

  const handleAsk = useCallback(
    (question: string) => {
      const text = question.trim();
      if (!text) return;
      const matches = searchFaq(text, fuse);
      const top = matches[0];
      const answer =
        top && top.score <= MATCH_SCORE_THRESHOLD
          ? t(top.entry.answerKey)
          : t('support.fallback');
      setMessages((prev) => [
        ...prev,
        { role: 'user', text },
        { role: 'bot', text: answer },
      ]);
      setInput('');
    },
    [fuse, t],
  );

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
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <span className="text-sm font-medium text-text">
                {t('support.panel.title')}
              </span>
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  toggleRef.current?.focus();
                }}
                aria-label={t('support.panel.close')}
                className="focus-ring press rounded-full p-1 text-muted hover:text-text"
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
                    <div
                      key={i}
                      className={
                        msg.role === 'user'
                          ? 'ml-auto max-w-[85%] rounded-[10px] bg-accent px-3 py-2 text-sm text-white'
                          : 'mr-auto max-w-[90%] rounded-[10px] bg-surface-2 px-3 py-2 text-sm text-text'
                      }
                    >
                      {msg.text}
                    </div>
                  ))}
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
