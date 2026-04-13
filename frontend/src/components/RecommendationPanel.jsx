import { Button, Card } from '@heroui/react'
import SelectionCards from './SelectionCards'
import DeploymentRow from './DeploymentRow'

const RATIONALE_KEYS = ['scope', 'backend', 'frontend', 'apis', 'database']

function coreLogicToBullets(text) {
  if (!text) return []
  const raw = String(text).replace(/\r\n/g, '\n').trim()
  if (!raw) return []

  const lines = raw
    .split('\n')
    .map(s => s.trim())
    .filter(Boolean)
    .map(s => s.replace(/^[-•]\s+/, ''))

  let bullets = lines.length > 1 ? lines : raw.split(/(?<=[.!?])\s+/).map(s => s.trim()).filter(Boolean)

  bullets = bullets
    .flatMap(s => s.split(/;\s+/).map(p => p.trim()).filter(Boolean))
    .map(s => s.replace(/\s+/g, ' '))
    .filter(Boolean)

  while (bullets.length < 4) {
    const idx = bullets.reduce((best, cur, i, arr) => (arr[i].length > arr[best].length ? i : best), 0)
    const parts = bullets[idx]?.split(/,\s+/).map(s => s.trim()).filter(Boolean) || []
    if (parts.length <= 1) break
    bullets.splice(idx, 1, ...parts)
  }

  return bullets.slice(0, 5)
}

export default function RecommendationPanel({
  summary, systemType, keyRequirements, rationale,
  coreSystemLogic, scopeBoundaries, phasedPlan,
  selections, onChange, architectureData, apiCandidates,
  deployment, onDeploymentChange, deploymentOptions,
  onGenerate,
}) {
  const overviewText = summary || 'No recommendation data yet. You can still choose a stack and continue.'
  const canGenerate = Boolean(
    selections.scope && selections.backend && selections.frontend && selections.database
  )

  return (
    <div className="flex flex-col gap-8">

      {/* 1. Overview */}
      <Card className="border border-accent/25">
        <Card.Content className="p-6">
          <div className="flex items-baseline justify-between gap-4 mb-2">
            <p className="text-xs font-bold uppercase tracking-widest text-accent">Overview</p>
            {systemType && (
              <p className="text-sm font-semibold text-foreground text-right">{systemType}</p>
            )}
          </div>
          <p className="text-foreground leading-relaxed">{overviewText}</p>
        </Card.Content>
      </Card>

      {/* 2. Core Logic + Key Requirements + Scope Boundaries */}
      {(coreSystemLogic || keyRequirements?.length > 0 || scopeBoundaries?.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {coreSystemLogic && (
            <Card>
              <Card.Content className="p-5">
                <p className="text-xs font-bold uppercase tracking-widest text-accent mb-2">Core Logic</p>
                <ul className="flex flex-col gap-1.5">
                  {coreLogicToBullets(coreSystemLogic).map((line, i) => (
                    <li
                      key={i}
                      className="text-sm text-foreground pl-3 relative before:content-['•'] before:absolute before:left-0 before:text-accent"
                    >
                      {line}
                    </li>
                  ))}
                </ul>
              </Card.Content>
            </Card>
          )}
          {keyRequirements?.length > 0 && (
            <Card>
              <Card.Content className="p-5">
                <p className="text-xs font-bold uppercase tracking-widest text-accent mb-2">Key Requirements</p>
                <ul className="flex flex-col gap-1.5">
                  {keyRequirements.map((req, i) => (
                    <li key={i} className="text-sm text-foreground pl-3 relative before:content-['•'] before:absolute before:left-0 before:text-accent">
                      {req}
                    </li>
                  ))}
                </ul>
              </Card.Content>
            </Card>
          )}
          {scopeBoundaries?.length > 0 && (
            <Card>
              <Card.Content className="p-5">
                <p className="text-xs font-bold uppercase tracking-widest text-accent mb-2">Scope Boundaries</p>
                <ul className="flex flex-col gap-1.5">
                  {scopeBoundaries.map((b, i) => (
                    <li key={i} className="text-sm text-foreground pl-3 relative before:content-['•'] before:absolute before:left-0 before:text-accent">
                      {b}
                    </li>
                  ))}
                </ul>
              </Card.Content>
            </Card>
          )}
        </div>
      )}

      {/* 3. Why This Setup */}
      {rationale && (
        <Card>
          <Card.Content className="p-5">
            <p className="text-xs font-bold uppercase tracking-widest text-accent mb-3">Why This Setup</p>
            <div className="flex flex-col gap-2.5">
              {RATIONALE_KEYS.map(key => rationale[key] && (
                <div key={key} className="grid grid-cols-[72px_1fr] gap-3 items-baseline">
                  <span className="text-[11px] font-bold uppercase tracking-wide text-muted pt-0.5">{key}</span>
                  <span className="text-sm text-foreground leading-relaxed">{rationale[key]}</span>
                </div>
              ))}
            </div>
          </Card.Content>
        </Card>
      )}

      {/* 4. Recommended Setup */}
      <div>
        <h2 className="text-base font-semibold mb-4">
          Recommended Setup{' '}
          <span className="text-muted font-normal text-sm">(fully editable)</span>
        </h2>
        <SelectionCards
          selections={selections}
          onChange={onChange}
          architectureData={architectureData}
          apiCandidates={apiCandidates}
        />
      </div>

      {/* 5. Deployment */}
      <div>
        <h2 className="text-base font-semibold mb-4">Deployment</h2>
        <DeploymentRow value={deployment} onChange={onDeploymentChange} deploymentOptions={deploymentOptions} />
      </div>

      <Button
        variant="primary"
        className="w-full"
        onPress={onGenerate}
        isDisabled={!canGenerate}
      >
        Generate Blueprint →
      </Button>
    </div>
  )
}
