import { useState } from 'react'

const DEFAULT_CONSTRAINTS = {
  user_scale: 'small',
  auth: 'none',
  data: { types: [], persistence: 'temporary' },
  execution: 'short',
  app_shape: 'simple',
}

function SegmentedControl({ options, value, onChange }) {
  return (
    <div className="segmented-control">
      {options.map(opt => (
        <button
          key={opt.value}
          type="button"
          className={`seg-btn${value === opt.value ? ' selected' : ''}`}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

function ChipGroup({ options, value, onChange, multi = false }) {
  function toggle(v) {
    if (multi) {
      onChange(value.includes(v) ? value.filter(x => x !== v) : [...value, v])
    } else {
      onChange(v)
    }
  }
  const isSelected = v => (multi ? value.includes(v) : value === v)
  return (
    <div className="chip-group">
      {options.map(opt => (
        <button
          key={opt.value}
          type="button"
          className={`chip${isSelected(opt.value) ? ' selected' : ''}`}
          onClick={() => toggle(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

export default function QuickSetupPanel({ onContinue }) {
  const [c, setC] = useState(DEFAULT_CONSTRAINTS)

  function set(key, value) {
    setC(prev => ({ ...prev, [key]: value }))
  }

  function setData(key, value) {
    setC(prev => ({ ...prev, data: { ...prev.data, [key]: value } }))
  }

  return (
    <div className="quicksetup-stage">
      <div className="quicksetup-header">
        <p className="quicksetup-title">Quick Setup</p>
        <p className="quicksetup-subtitle">5 questions · ~15 seconds</p>
      </div>

      <div className="quicksetup-questions">

        {/* 1. Users & Scale */}
        <div className="qs-block">
          <p className="qs-label">Who's using this?</p>
          <SegmentedControl
            value={c.user_scale}
            onChange={v => set('user_scale', v)}
            options={[
              { value: 'single', label: 'Just me' },
              { value: 'small', label: 'Small group' },
              { value: 'large', label: 'Larger audience' },
            ]}
          />
        </div>

        {/* 2. Accounts / Identity */}
        <div className="qs-block">
          <p className="qs-label">Accounts / login?</p>
          <ChipGroup
            value={c.auth}
            onChange={v => set('auth', v)}
            options={[
              { value: 'none', label: 'No accounts' },
              { value: 'simple', label: 'Email / magic link' },
              { value: 'oauth', label: 'Social login' },
            ]}
          />
        </div>

        {/* 3. Data & Storage */}
        <div className="qs-block">
          <p className="qs-label">What data does it handle?</p>
          <ChipGroup
            value={c.data.types}
            onChange={v => setData('types', v)}
            multi
            options={[
              { value: 'none', label: 'No storage' },
              { value: 'text', label: 'Text / data' },
              { value: 'files', label: 'Files (PDFs, images)' },
              { value: 'results', label: 'Saved history' },
            ]}
          />
          <div className="qs-toggle-row">
            <span className="qs-toggle-label">Save long-term?</span>
            <SegmentedControl
              value={c.data.persistence}
              onChange={v => setData('persistence', v)}
              options={[
                { value: 'temporary', label: 'Temporary' },
                { value: 'permanent', label: 'Persistent' },
              ]}
            />
          </div>
        </div>

        {/* 4. Speed / Execution */}
        <div className="qs-block">
          <p className="qs-label">How fast does it need to respond?</p>
          <SegmentedControl
            value={c.execution}
            onChange={v => set('execution', v)}
            options={[
              { value: 'realtime', label: 'Instant' },
              { value: 'short', label: 'Few seconds' },
              { value: 'async', label: 'Background' },
            ]}
          />
        </div>

        {/* 5. App Shape */}
        <div className="qs-block">
          <p className="qs-label">What shape is this app?</p>
          <ChipGroup
            value={c.app_shape}
            onChange={v => set('app_shape', v)}
            options={[
              { value: 'simple', label: 'Simple tool' },
              { value: 'ai_core', label: 'AI-powered tool' },
              { value: 'workflow', label: 'Multi-step workflow' },
            ]}
          />
        </div>

      </div>

      <button className="btn-primary" onClick={() => onContinue(c)}>
        Continue →
      </button>
    </div>
  )
}
