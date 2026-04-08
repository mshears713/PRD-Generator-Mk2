import SelectionCards from './SelectionCards'

export default function RecommendationPanel({ summary, selections, onChange, onGenerate }) {
  const canGenerate = Boolean(
    selections.scope && selections.backend && selections.frontend && selections.database
  )

  return (
    <div className="recommendation-stage">
      <div className="summary-card">
        <p className="summary-label">System Understanding</p>
        <p className="summary-text">{summary}</p>
      </div>

      <div>
        <h2 className="section-title">
          Recommended Setup{' '}
          <span className="editable-note">(fully editable)</span>
        </h2>
        <SelectionCards selections={selections} onChange={onChange} />
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
