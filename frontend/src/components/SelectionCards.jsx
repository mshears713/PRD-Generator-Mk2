import { Button, Input } from '@heroui/react'
import DecisionCard from './DecisionCard'
import { STACK_DETAILS, API_DETAILS } from '../data/options'

const OPTIONS = {
  scope: ['frontend', 'backend', 'fullstack'],
  backend: ['fastapi', 'node', 'none'],
  frontend: ['react', 'static', 'none'],
  apis: ['openrouter', 'tavily'],
  database: ['postgres', 'firebase', 'none'],
}

const LABELS = {
  scope: 'Scope',
  backend: 'Backend',
  frontend: 'Frontend',
  apis: 'APIs (multi-select)',
  database: 'Database',
}

function resolveDetail(field, value, architectureData) {
  if (!value) return null
  const staticDetail = STACK_DETAILS[field]?.[value]
  if (!staticDetail) return null
  const backendOption = architectureData?.[field]?.options?.[value]
  return {
    name: staticDetail.name,
    subtitle: staticDetail.subtitle,
    learnMoreUrl: staticDetail.learnMoreUrl || null,
    reason: backendOption?.reason || null,
    benefits: backendOption?.benefits?.length ? backendOption.benefits : staticDetail.benefits,
    drawbacks: backendOption?.drawbacks?.length ? backendOption.drawbacks : staticDetail.drawbacks,
  }
}

function StackGroup({ field, selections, onSelect, architectureData }) {
  const selected = selections[field]
  const recommended = architectureData?.[field]?.recommended
  const detail = resolveDetail(field, selected, architectureData)

  const visibleOptions = OPTIONS[field].filter(opt => {
    const optData = architectureData?.[field]?.options?.[opt]
    return !optData || optData.relevant !== false
  })

  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs font-bold uppercase tracking-wide text-muted">
        {LABELS[field]}
      </label>
      <div className="flex flex-wrap gap-2">
        {visibleOptions.map(opt => {
          const staticMeta = STACK_DETAILS[field]?.[opt]
          const isRec = opt === recommended
          const isSelected = selected === opt
          return (
            <Button
              key={opt}
              variant={isSelected ? 'secondary' : 'outline'}
              size="sm"
              onPress={() => onSelect(field, opt)}
              className="capitalize"
            >
              {staticMeta?.name || opt}
              {isRec && <span className="ml-1.5 text-accent text-[10px]">★</span>}
            </Button>
          )
        })}
      </div>
      {detail && selected && (
        <DecisionCard
          title={detail.name}
          subtitle={detail.subtitle}
          learnMoreUrl={detail.learnMoreUrl}
          reason={detail.reason}
          benefits={detail.benefits}
          drawbacks={detail.drawbacks}
          isRecommended={selected === recommended}
        />
      )}
    </div>
  )
}

export default function SelectionCards({ selections, onChange, architectureData }) {
  function selectSingle(field, value) {
    onChange({ ...selections, [field]: value })
  }

  function toggleApi(api) {
    const current = selections.apis || []
    const next = current.includes(api)
      ? current.filter(a => a !== api)
      : [...current, api]
    const api_keys = { ...selections.api_keys }
    if (!next.includes(api)) delete api_keys[api]
    onChange({ ...selections, apis: next, api_keys })
  }

  function setApiKey(api, value) {
    onChange({ ...selections, api_keys: { ...selections.api_keys, [api]: value } })
  }

  const selectedApis = selections.apis || []

  return (
    <div className="flex flex-col gap-6">

      {['scope', 'backend', 'frontend'].map(field => (
        <StackGroup
          key={field}
          field={field}
          selections={selections}
          onSelect={selectSingle}
          architectureData={architectureData}
        />
      ))}

      {/* APIs — multi-select */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-bold uppercase tracking-wide text-muted">
          {LABELS.apis}
        </label>
        <div className="flex flex-wrap gap-2">
          {OPTIONS.apis.map(api => {
            const meta = API_DETAILS[api]
            const isSelected = selectedApis.includes(api)
            return (
              <Button
                key={api}
                variant={isSelected ? 'secondary' : 'outline'}
                size="sm"
                onPress={() => toggleApi(api)}
                className={meta?.sponsored ? 'border-warning/55' : ''}
              >
                {meta?.name || api}
                {meta?.sponsored && <span className="ml-1.5 text-warning text-[10px]">✦</span>}
              </Button>
            )
          })}
        </div>

        {selectedApis.map(api => {
          const meta = API_DETAILS[api]
          if (!meta) return null
          return (
            <DecisionCard
              key={api}
              title={meta.name}
              subtitle={meta.subtitle}
              learnMoreUrl={meta.learnMoreUrl}
              benefits={meta.benefits}
              drawbacks={meta.drawbacks}
              sponsored={meta.sponsored}
              sponsorOffer={meta.sponsorOffer}
            />
          )
        })}

        {selectedApis.map(api => (
          <div key={`key-${api}`} className="flex flex-col gap-1">
            <label className="text-xs text-muted capitalize">
              {API_DETAILS[api]?.name || api} API key
            </label>
            <Input
              type="text"
              placeholder={`Enter your ${API_DETAILS[api]?.name || api} key...`}
              value={selections.api_keys?.[api] || ''}
              onChange={e => setApiKey(api, e.target.value)}
              aria-label={`${API_DETAILS[api]?.name || api} API key`}
              className="max-w-sm font-mono"
            />
          </div>
        ))}
      </div>

      {/* Database */}
      <StackGroup
        field="database"
        selections={selections}
        onSelect={selectSingle}
        architectureData={architectureData}
      />

    </div>
  )
}
