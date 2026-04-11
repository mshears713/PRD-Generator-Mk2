import { Button } from '@heroui/react'
import DecisionCard from './DecisionCard'
import { DEPLOYMENT_OPTIONS } from '../data/options'

function getSponsorOffer(opt) {
  if (opt.sponsor_info) {
    const { why_use = [], bonus = '' } = opt.sponsor_info
    return [why_use[0], bonus].filter(Boolean).join(' — ')
  }
  return opt.sponsorOffer || ''
}

function mergeOption(backendOpt) {
  const staticOpt = DEPLOYMENT_OPTIONS.find(s => s.value === backendOpt.value) || {}
  return { ...staticOpt, ...backendOpt, subtitle: staticOpt.subtitle }
}

export default function DeploymentRow({ value, onChange, deploymentOptions }) {
  const options = deploymentOptions?.length
    ? deploymentOptions.map(mergeOption)
    : DEPLOYMENT_OPTIONS

  const selected = options.find(o => o.value === value)

  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs font-bold uppercase tracking-wide text-muted">Deployment</label>
      <div className="flex flex-wrap gap-2">
        {options.map(opt => (
          <Button
            key={opt.value}
            variant={value === opt.value ? 'secondary' : 'outline'}
            size="sm"
            onPress={() => onChange(opt.value)}
            className={opt.sponsored ? 'border-warning/55' : ''}
          >
            {opt.name}
            {opt.sponsored && <span className="ml-1.5 text-warning text-[10px]">✦</span>}
          </Button>
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
