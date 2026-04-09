import SelectionCards from './SelectionCards'
import DeploymentRow from './DeploymentRow'

const RATIONALE_KEYS = ['scope', 'backend', 'frontend', 'apis', 'database']

export default function RecommendationPanel({
  summary, systemType, keyRequirements, rationale,
  coreSystemLogic, scopeBoundaries, phasedPlan,
  selections, onChange, architectureData,
  deployment, onDeploymentChange, deploymentOptions,
  onGenerate,
}) {
  const canGenerate = Boolean(
    selections.scope && selections.backend && selections.frontend && selections.database
  )

  return (
    <div className="recommendation-stage">

      {/* ── 1. Overview (hero, full-width) with system type tag inline ───── */}
      <div className="summary-card summary-card-hero">
        <div className="overview-header">
          <p className="summary-label">Overview</p>
          {systemType && <span className="system-type-tag">{systemType}</span>}
        </div>
        <p className="summary-text summary-text-hero">{summary}</p>
      </div>

      {/* ── 2. Core Logic + Key Requirements + Scope Boundaries (3-col) ──── */}
      {(coreSystemLogic || keyRequirements?.length > 0 || scopeBoundaries?.length > 0) && (
        <div className="insight-grid insight-grid-3">
          {coreSystemLogic && (
            <div className="summary-card">
              <p className="summary-label">Core Logic</p>
              <p className="summary-text">{coreSystemLogic}</p>
            </div>
          )}
          {keyRequirements?.length > 0 && (
            <div className="summary-card">
              <p className="summary-label">Key Requirements</p>
              <ul className="requirements-list">
                {keyRequirements.map((req, i) => <li key={i}>{req}</li>)}
              </ul>
            </div>
          )}
          {scopeBoundaries?.length > 0 && (
            <div className="summary-card">
              <p className="summary-label">Scope Boundaries</p>
              <ul className="requirements-list">
                {scopeBoundaries.map((b, i) => <li key={i}>{b}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* ── 3. Why This Setup (full-width row) ───────────────────────────── */}
      {rationale && (
        <div className="summary-card">
          <p className="summary-label">Why This Setup</p>
          <div className="rationale-grid">
            {RATIONALE_KEYS.map(key => rationale[key] && (
              <div key={key} className="rationale-row">
                <span className="rationale-key">{key}</span>
                <span className="rationale-val">{rationale[key]}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 4. Recommended Setup ─────────────────────────────────────────── */}
      <div>
        <h2 className="section-title">
          Recommended Setup{' '}
          <span className="editable-note">(fully editable)</span>
        </h2>
        <SelectionCards selections={selections} onChange={onChange} architectureData={architectureData} />
      </div>

      {/* ── 5. Deployment ────────────────────────────────────────────────── */}
      <div>
        <h2 className="section-title">Deployment</h2>
        <DeploymentRow value={deployment} onChange={onDeploymentChange} deploymentOptions={deploymentOptions} />
      </div>

      <button
        className="btn-primary"
        onClick={onGenerate}
        disabled={!canGenerate}
      >
        Generate Blueprint →
      </button>
    </div>
  )
}
