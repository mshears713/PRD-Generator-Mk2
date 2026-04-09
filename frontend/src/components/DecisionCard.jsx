function SponsoredBadge() {
  return <span className="sponsored-badge">✦ Sponsored</span>
}

/**
 * DecisionCard — shows the tradeoffs for a selected stack/API/deployment option.
 *
 * Props:
 *   title        string   — display name (e.g. "FastAPI")
 *   subtitle     string   — short descriptor
 *   benefits     string[] — ✅ bullet points (2–4)
 *   drawbacks    string[] — ❌ bullet points (2–4)
 *   sponsored    bool     — shows sponsored badge + offer
 *   sponsorOffer string   — one-line offer text
 */
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
  return (
    <div className={[
      'decision-card',
      sponsored ? 'decision-card-sponsored' : '',
      isRecommended ? 'decision-card-recommended' : '',
    ].filter(Boolean).join(' ')}>

      <div className="dc-header">
        <div className="dc-titles">
          <span className="dc-name">{title}</span>
          <span className="dc-sub">{subtitle}</span>
        </div>
        {sponsored && <SponsoredBadge />}
      </div>

      {reason && <p className="dc-reason">{reason}</p>}

      {sponsored && sponsorOffer && (
        <div className="dc-sponsor-offer">{sponsorOffer}</div>
      )}

      <div className="dc-columns">
        <div className="dc-col">
          <p className="dc-col-label dc-benefits-label">✅ Benefits</p>
          <ul className="dc-list">
            {benefits.map((b, i) => <li key={i}>{b}</li>)}
          </ul>
        </div>
        <div className="dc-col">
          <p className="dc-col-label dc-drawbacks-label">❌ Drawbacks</p>
          <ul className="dc-list">
            {drawbacks.map((d, i) => <li key={i}>{d}</li>)}
          </ul>
        </div>
      </div>

      {learnMoreUrl && (
        <a
          href={learnMoreUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="dc-learn-more"
        >
          Learn more ↗
        </a>
      )}

    </div>
  )
}
