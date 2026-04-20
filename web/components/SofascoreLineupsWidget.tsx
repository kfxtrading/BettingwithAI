const WIDGET_BASE_URL = 'https://widgets.sofascore.com/embed/lineups';

type Props = {
  eventId: number;
  homeTeam: string;
  awayTeam: string;
};

export function SofascoreLineupsWidget({
  eventId,
  homeTeam,
  awayTeam,
}: Props) {
  const src = `${WIDGET_BASE_URL}?id=${eventId}&widgetTheme=dark`;
  return (
    <iframe
      id={`sofa-lineups-embed-${eventId}`}
      src={src}
      title={`Sofascore lineups: ${homeTeam} vs ${awayTeam}`}
      loading="lazy"
      scrolling="no"
      frameBorder={0}
      sandbox="allow-scripts allow-same-origin allow-popups"
      referrerPolicy="no-referrer-when-downgrade"
      className="mx-auto block h-[786px] w-full max-w-[480px] rounded-md border border-white/10 bg-bg"
    />
  );
}
