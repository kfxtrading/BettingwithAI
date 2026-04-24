import { JsonLd } from '@/components/JsonLd';
import { faqPageLd } from '@/lib/seo';
import type { FaqItem } from '@/content/home-faq';

type FaqSectionProps = {
  /** Section heading (visually above the list). */
  heading?: string;
  /** Optional short intro sentence. */
  intro?: string;
  /** Q&A items to render. */
  items: readonly FaqItem[];
  /** Optional "Last updated" ISO date to display for freshness signals. */
  lastUpdated?: string;
  /** When false, the FAQPage JSON-LD is omitted (use when another page already emits it). */
  emitJsonLd?: boolean;
};

/**
 * Accessible FAQ accordion rendered with native <details>/<summary> so it
 * stays crawlable and keyboard-navigable without JavaScript. Emits
 * `FAQPage` schema.org JSON-LD for rich-results eligibility.
 */
export function FaqSection({
  heading = 'Frequently asked questions',
  intro,
  items,
  lastUpdated,
  emitJsonLd = true,
}: FaqSectionProps) {
  if (items.length === 0) return null;
  return (
    <section className="mt-12" aria-labelledby="faq-heading">
      {emitJsonLd ? <JsonLd data={faqPageLd(items)} /> : null}
      <header className="mb-5">
        <h2
          id="faq-heading"
          className="text-lg font-medium tracking-tight text-text"
        >
          {heading}
        </h2>
        {intro ? (
          <p className="mt-1 text-sm text-muted">{intro}</p>
        ) : null}
        {lastUpdated ? (
          <p className="mt-1 text-2xs uppercase tracking-[0.08em] text-muted">
            Last updated{' '}
            <time dateTime={lastUpdated}>{lastUpdated}</time>
          </p>
        ) : null}
      </header>
      <div className="divide-y divide-white/10 rounded-md border border-white/10 bg-surface-1">
        {items.map((item, i) => (
          <details
            key={i}
            className="group px-4 py-3 open:bg-white/[0.03]"
          >
            <summary className="flex cursor-pointer list-none items-start justify-between gap-4 text-sm font-medium text-text">
              <span>{item.question}</span>
              <span
                aria-hidden="true"
                className="mt-1 text-muted transition-transform group-open:rotate-45"
              >
                +
              </span>
            </summary>
            <p className="mt-3 text-sm leading-relaxed text-muted">
              {item.answer}
            </p>
          </details>
        ))}
      </div>
    </section>
  );
}
