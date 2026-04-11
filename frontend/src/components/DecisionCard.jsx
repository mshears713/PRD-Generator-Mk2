import { Card, Chip, Link } from '@heroui/react'

function SponsoredBadge() {
  return <Chip size="sm" color="warning" variant="soft">✦ Sponsored</Chip>
}

export default function DecisionCard({
  title,
  subtitle,
  reason,
  learnMoreUrl,
  benefits = [],
  drawbacks = [],
  sponsored = false,
  sponsorOffer = '',
  isRecommended = false,
}) {
  const borderClass = sponsored
    ? 'border border-warning/55'
    : isRecommended
    ? 'border border-accent/70'
    : ''

  return (
    <Card className={`mt-2 ${borderClass}`}>
      <Card.Content className="p-4 flex flex-col gap-2">

        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-semibold text-foreground">{title}</span>
            <span className="text-xs text-muted">{subtitle}</span>
          </div>
          {sponsored && <SponsoredBadge />}
        </div>

        {reason && (
          <p className="text-xs text-muted italic leading-relaxed">{reason}</p>
        )}

        {sponsored && sponsorOffer && (
          <div className="bg-accent/8 border border-accent/20 rounded-md px-3 py-2 text-xs text-foreground leading-relaxed">
            {sponsorOffer}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 mt-1">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-success mb-1.5">✅ Benefits</p>
            <ul className="flex flex-col gap-1">
              {benefits.map((b, i) => (
                <li key={i} className="text-xs text-muted leading-relaxed">{b}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-danger mb-1.5">❌ Drawbacks</p>
            <ul className="flex flex-col gap-1">
              {drawbacks.map((d, i) => (
                <li key={i} className="text-xs text-muted leading-relaxed">{d}</li>
              ))}
            </ul>
          </div>
        </div>

        {learnMoreUrl && (
          <Link
            href={learnMoreUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-muted mt-1 self-start"
          >
            Learn more
            <Link.Icon />
          </Link>
        )}

      </Card.Content>
    </Card>
  )
}
