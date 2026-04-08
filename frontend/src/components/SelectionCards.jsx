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

export default function SelectionCards({ selections, onChange }) {
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

  return (
    <div className="selection-cards">
      {['scope', 'backend', 'frontend'].map(field => (
        <div className="card-group" key={field}>
          <label className="card-group-label">{LABELS[field]}</label>
          <div className="card-row">
            {OPTIONS[field].map(opt => (
              <button
                key={opt}
                className={`card-btn${selections[field] === opt ? ' selected' : ''}`}
                onClick={() => selectSingle(field, opt)}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      ))}

      <div className="card-group">
        <label className="card-group-label">{LABELS.apis}</label>
        <div className="card-row">
          {OPTIONS.apis.map(api => (
            <button
              key={api}
              className={`card-btn${(selections.apis || []).includes(api) ? ' selected' : ''}`}
              onClick={() => toggleApi(api)}
            >
              {api}
            </button>
          ))}
        </div>
        {(selections.apis || []).map(api => (
          <div className="api-key-input" key={api}>
            <label>{api} API key</label>
            <input
              type="text"
              placeholder={`Enter your ${api} key...`}
              value={selections.api_keys?.[api] || ''}
              onChange={e => setApiKey(api, e.target.value)}
            />
          </div>
        ))}
      </div>

      <div className="card-group">
        <label className="card-group-label">{LABELS.database}</label>
        <div className="card-row">
          {OPTIONS.database.map(opt => (
            <button
              key={opt}
              className={`card-btn${selections.database === opt ? ' selected' : ''}`}
              onClick={() => selectSingle('database', opt)}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
