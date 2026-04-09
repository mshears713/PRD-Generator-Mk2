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

/**
 * Build the DecisionCard props for a selected stack option.
 * Backend data (benefits/drawbacks/reason) always wins over static.
 * Static data provides name and subtitle (backend doesn't include these).
 */
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

// Single-select field group with a DecisionCard detail panel for the selected option
function StackGroup({ field, selections, onSelect, architectureData }) {
  const selected = selections[field]
  const recommended = architectureData?.[field]?.recommended
  const detail = resolveDetail(field, selected, architectureData)

  // Only show options that are relevant (or all if no advice yet)
  const visibleOptions = OPTIONS[field].filter(opt => {
    const optData = architectureData?.[field]?.options?.[opt]
    return !optData || optData.relevant !== false
  })

  return (
    <div className="card-group">
      <label className="card-group-label">{LABELS[field]}</label>
      <div className="card-row">
        {visibleOptions.map(opt => {
          const staticMeta = STACK_DETAILS[field]?.[opt]
          const isRec = opt === recommended
          return (
            <button
              key={opt}
              type="button"
              className={`card-btn${selected === opt ? ' selected' : ''}${isRec ? ' card-btn-recommended' : ''}`}
              onClick={() => onSelect(field, opt)}
            >
              {staticMeta?.name || opt}
              {isRec && <span className="card-rec-badge" title="Recommended">★</span>}
            </button>
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
    <div className="selection-cards">

      {/* Scope / Backend / Frontend — each with a backend-aware detail panel */}
      {['scope', 'backend', 'frontend'].map(field => (
        <StackGroup
          key={field}
          field={field}
          selections={selections}
          onSelect={selectSingle}
          architectureData={architectureData}
        />
      ))}

      {/* APIs — multi-select chips with sponsored badges, DecisionCard per selected */}
      <div className="card-group">
        <label className="card-group-label">{LABELS.apis}</label>
        <div className="card-row">
          {OPTIONS.apis.map(api => {
            const meta = API_DETAILS[api]
            const isSelected = selectedApis.includes(api)
            return (
              <button
                key={api}
                type="button"
                className={`card-btn${isSelected ? ' selected' : ''}${meta?.sponsored ? ' card-btn-sponsored' : ''}`}
                onClick={() => toggleApi(api)}
              >
                {meta?.name || api}
                {meta?.sponsored && <span className="card-sponsored-star" title="Sponsored">✦</span>}
              </button>
            )
          })}
        </div>

        {/* DecisionCard for each selected API (always uses static sponsored data) */}
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

        {/* API key inputs */}
        {selectedApis.map(api => (
          <div className="api-key-input" key={`key-${api}`}>
            <label>{API_DETAILS[api]?.name || api} API key</label>
            <input
              type="text"
              placeholder={`Enter your ${API_DETAILS[api]?.name || api} key...`}
              value={selections.api_keys?.[api] || ''}
              onChange={e => setApiKey(api, e.target.value)}
            />
          </div>
        ))}
      </div>

      {/* Database — with backend-aware detail panel */}
      <StackGroup
        field="database"
        selections={selections}
        onSelect={selectSingle}
        architectureData={architectureData}
      />

    </div>
  )
}
