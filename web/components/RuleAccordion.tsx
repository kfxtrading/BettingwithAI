'use client';

import { ChevronDown } from 'lucide-react';
import type { ReactNode } from 'react';

function Item({
  summary,
  children,
}: {
  summary: string;
  children: ReactNode;
}) {
  return (
    <details className="surface-card group px-5 py-3 text-sm">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium">
        <span>{summary}</span>
        <ChevronDown
          size={16}
          className="text-muted transition-transform group-open:rotate-180"
        />
      </summary>
      <div className="mt-3 text-muted">{children}</div>
    </details>
  );
}

export function RuleAccordion() {
  return (
    <div className="flex flex-col gap-3">
      <Item summary="Regel-Details">
        <ul className="list-inside list-disc space-y-1">
          <li>Startkapital: 100 Punkte (intern € 1.000)</li>
          <li>
            Wette wird platziert, wenn Modell-Edge ≥ 3 % und Quote zwischen
            1,30 und 15,00
          </li>
          <li>Nur 1X2-Märkte (Heim / Unentschieden / Auswärts)</li>
          <li>Einsatz: Quarter-Kelly (0,25 × optimaler Kelly-Bruch)</li>
          <li>Hardcap: maximal 5 % des aktuellen Kontostands pro Wette</li>
          <li>Keine Kombiwetten, keine Sonderwetten</li>
          <li>
            Einsatz wird vor jedem Spiel auf Basis der aktuellen Bankroll
            neu berechnet
          </li>
        </ul>
      </Item>
      <Item summary="Wie wird berechnet?">
        <p>
          Der Performance-Index ist eine normalisierte Darstellung der
          simulierten Bankroll: <code>index(t) = 100 × balance(t) / 1000</code>.
          Ein Wert von 110 entspricht einem simulierten Plus von 10 %.
        </p>
        <p className="mt-2">
          Jeder Tag in der Kurve ist ein Kalendertag — an Tagen ohne
          Wettabschluss bleibt der Index unverändert. Max Drawdown zeigt
          den größten Peak-to-Trough-Verlust seit Tracking-Start.
        </p>
      </Item>
      <Item summary="Kein Finanzrat">
        <p>
          Hypothetische Simulation eines statistischen Modells auf Basis
          vergangener Spieldaten. Keine Aufforderung zum Glücksspiel. Keine
          Gewähr auf zukünftige Ergebnisse. Glücksspiele bergen finanzielle
          Risiken. Hilfe unter{' '}
          <a
            href="https://www.bundesweite-suchtberatung.de"
            target="_blank"
            rel="noreferrer"
            className="underline hover:text-text"
          >
            bundesweite-suchtberatung.de
          </a>{' '}
          oder Tel. 0800 1 372 700. Nur für Personen ab 18 Jahren.
        </p>
      </Item>
    </div>
  );
}
