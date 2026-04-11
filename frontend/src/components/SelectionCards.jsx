import React, { useMemo, useState } from 'react'
import { Button, Chip, Input } from '@heroui/react'
import DecisionCard from './DecisionCard'
import { STACK_DETAILS } from '../data/options'

const OPTIONS = {
  scope: ['frontend', 'backend', 'fullstack'],
  backend: ['fastapi', 'node', 'none'],
  frontend: ['react', 'static', 'none'],
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

function normalizeApiCandidates(apiCandidates) {
  if (!apiCandidates) return { selectable: [], rejected: [], meta: {} }
  const meta = {}
  const selectable = []
  const rejected = []
  ;['selected', 'candidates'].forEach(statusKey => {
    (apiCandidates[statusKey] || []).forEach(item => {
      meta[item.id] = item
      selectable.push(item)
    })
  })
  ;(apiCandidates.rejected || []).forEach(item => {
    meta[item.id] = item
    rejected.push(item)
  })
  return { selectable, rejected, meta }
}

export default function SelectionCards({ selections, onChange, architectureData, apiCandidates }) {
  const [activeApi, setActiveApi] = useState('')
  const [showDatabaseOptions, setShowDatabaseOptions] = useState(false)

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
  const { selectable: availableApis, rejected: rejectedApis, meta: apiMeta } = normalizeApiCandidates(apiCandidates)
  const activeApiId = activeApi && apiMeta[activeApi] ? activeApi : (selectedApis[0] || '')
  const activeMeta = activeApiId ? apiMeta[activeApiId] : null

  const databaseRelevant = selections.database && selections.database !== 'none'
  const filteredAvailableApis = useMemo(() => {
    const items = [...availableApis]
    items.sort((a, b) => {
      const recA = a.recommended ? 1 : 0
      const recB = b.recommended ? 1 : 0
      if (recA !== recB) return recB - recA
      const selA = a.status === 'selected' ? 1 : 0
      const selB = b.status === 'selected' ? 1 : 0
      if (selA !== selB) return selB - selA
      return (a.name || a.id).localeCompare(b.name || b.id)
    })

    if (databaseRelevant) return items
    return items.filter(item => !(item.category === 'database' && (item.id === 'postgres' || item.id === 'supabase')))
  }, [availableApis, databaseRelevant])

  const filteredRejectedApis = useMemo(() => {
    if (databaseRelevant) return rejectedApis
    return rejectedApis.filter(item => !(item.category === 'database' && (item.id === 'postgres' || item.id === 'supabase')))
  }, [rejectedApis, databaseRelevant])

  const shouldShowDatabasePicker =
    showDatabaseOptions ||
    (architectureData?.database?.recommended && architectureData.database.recommended !== 'none') ||
    (selections.database && selections.database !== 'none')

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
          {filteredAvailableApis.map(item => {
            const isSelected = selectedApis.includes(item.id)
            const variant = isSelected ? 'secondary' : item.status === 'selected' ? 'flat' : 'outline'
            return (
              <Button
                key={item.id}
                variant={variant}
                size="sm"
                onPress={() => {
                  setActiveApi(item.id)
                  toggleApi(item.id)
                }}
                className={item.sponsored ? 'border-warning/55' : ''}
              >
                {item.name || item.id}
                {item.recommended && <span className="ml-1.5 text-accent text-[10px]">★</span>}
                {item.sponsored && <span className="ml-1.5 text-warning text-[10px]">✦</span>}
              </Button>
            )
          })}
          {filteredAvailableApis.length === 0 && (
            <span className="text-sm text-muted">No API tools needed for this idea.</span>
          )}
        </div>

        {activeMeta && (
          <DecisionCard
            title={activeMeta.name || activeApiId}
            subtitle={activeMeta.summary || activeMeta.category}
            learnMoreUrl={null}
            reason={activeMeta.reason}
            benefits={(activeMeta.best_for || []).slice(0, 3)}
            drawbacks={(activeMeta.avoid_when || []).slice(0, 2)}
            sponsored={activeMeta.sponsored}
            sponsorOffer={activeMeta.sponsor_note}
            isRecommended={activeMeta.recommended}
          />
        )}

        {activeApiId && selectedApis.includes(activeApiId) && (
          <div className="flex flex-col gap-1 mt-2">
            <label className="text-xs text-muted capitalize">
              {(activeMeta?.name || activeApiId)} API key
            </label>
            <Input
              type="text"
              placeholder={`Enter your ${activeMeta?.name || activeApiId} key...`}
              value={selections.api_keys?.[activeApiId] || ''}
              onChange={e => setApiKey(activeApiId, e.target.value)}
              aria-label={`${activeMeta?.name || activeApiId} API key`}
              className="max-w-sm font-mono"
            />
          </div>
        )}

        {filteredRejectedApis.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {filteredRejectedApis.map(item => (
              <Chip key={item.id} size="sm" variant="flat" color="default">
                {item.name || item.id}: {item.why_not || 'Not needed'}
              </Chip>
            ))}
          </div>
        )}
      </div>

      {/* Database */}
      {shouldShowDatabasePicker ? (
        <StackGroup
          field="database"
          selections={selections}
          onSelect={(field, value) => {
            setShowDatabaseOptions(true)
            selectSingle(field, value)
          }}
          architectureData={architectureData}
        />
      ) : (
        <div className="bg-surface border border-border rounded-lg p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-accent">Database</p>
              <p className="text-sm text-muted mt-1">No persistent storage needed for this plan.</p>
            </div>
            <Button size="sm" variant="outline" onPress={() => setShowDatabaseOptions(true)}>
              Add a database
            </Button>
          </div>
        </div>
      )}

    </div>
  )
}
