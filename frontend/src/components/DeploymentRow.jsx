import DecisionCard from './DecisionCard'
import { DEPLOYMENT_OPTIONS } from '../data/options'

/**
 * Normalize a deployment option from the backend or static source into
 * the shape DecisionCard expects (sponsorOffer as a single string).
 */
function getSponsorOffer(opt) {
  if (opt.sponsor_info) {
    const { why_use = [], bonus = '' } = opt.sponsor_info
    return [why_use[0], bonus].filter(Boolean).join(' — ')
  }
  return opt.sponsorOffer || ''
}

/**
 * Merge a backend deployment option with its static counterpart.
 * Backend wins for benefits, drawbacks, recommended, reason.
 * Static wins for subtitle (backend doesn't provide this).
 */
function mergeOption(backendOpt) {
  const staticOpt = DEPLOYMENT_OPTIONS.find(s => s.value === backendOpt.value) || {}
  return { ...staticOpt, ...backendOpt, subtitle: staticOpt.subtitle }
}

export default function DeploymentRow({ value, onChange, deploymentOptions }) {
  // Prefer backend options (merged with static subtitles); fall back to static only
  const options = deploymentOptions?.length
    ? deploymentOptions.map(mergeOption)
    : DEPLOYMENT_OPTIONS

  const selected = options.find(o => o.value === value)

  return (
    <div className="card-group">
      <label className="card-group-label">Deployment</label>

      <div className="card-row">
        {options.map(opt => (
          <button
            key={opt.value}
            type="button"
            className={`card-btn${value === opt.value ? ' selected' : ''}${opt.sponsored ? ' card-btn-sponsored' : ''}`}
            onClick={() => onChange(opt.value)}
          >
            {opt.name}
            {opt.sponsored && <span className="card-sponsored-star" title="Sponsored">✦</span>}
          </button>
        ))}
      </div>

      {selected && (
        <DecisionCard
          title={selected.name}
          subtitle={selected.subtitle}
          reason={selected.reason_for_recommendation}
          benefits={selected.benefits}
          drawbacks={selected.drawbacks}
          sponsored={selected.sponsored}
          sponsorOffer={getSponsorOffer(selected)}
          isRecommended={selected.recommended === true}
        />
      )}
    </div>
  )
}
