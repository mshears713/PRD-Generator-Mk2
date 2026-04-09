import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  function copy() {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button className="copy-btn" onClick={copy}>
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

const GROWTH_SECTIONS = [
  { key: 'good',     icon: '✅', label: 'Good Choices',       cardClass: 'growth-card growth-card-good' },
  { key: 'warnings', icon: '⚠️', label: 'Warnings',           cardClass: 'growth-card growth-card-warn' },
  { key: 'missing',  icon: '❌', label: 'Still Missing',       cardClass: 'growth-card growth-card-missing' },
]

function GrowthCheckCards({ data }) {
  const [expanded, setExpanded] = useState({})
  if (!data || typeof data !== 'object') return null

  function toggle(key, i) {
    const id = `${key}-${i}`
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }))
  }

  return (
    <div className="growth-cards-row">
      {GROWTH_SECTIONS.map(({ key, icon, label, cardClass }) => (
        <div key={key} className={cardClass}>
          <div className="growth-card-title">{icon} {label}</div>
          <ul className="growth-items">
            {(data[key] || []).map((item, i) => (
              <li key={i} className="growth-item">
                <button
                  className="growth-item-btn"
                  onClick={() => toggle(key, i)}
                  aria-expanded={!!expanded[`${key}-${i}`]}
                >
                  <span className="growth-item-title">{item.title}</span>
                  <span className="growth-expand-icon">{expanded[`${key}-${i}`] ? '▲' : '▼'}</span>
                </button>
                {expanded[`${key}-${i}`] && (
                  <p className="growth-item-detail">{item.detail}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

export default function OutputPanel({ output, onReset }) {
  return (
    <div className="output-stage">

      <div className="output-section">
        <h2 className="output-section-title">Growth Check</h2>
        <GrowthCheckCards data={output.growth_check} />
      </div>

      <div className="output-section">
        <h2 className="output-section-title">PRD</h2>
        <div className="markdown-body">
          <ReactMarkdown>{output.prd}</ReactMarkdown>
        </div>
      </div>

      <div className="output-section">
        <div className="output-section-header">
          <h2 className="output-section-title">.env</h2>
          <CopyButton text={output.env} />
        </div>
        <pre className="env-block">{output.env}</pre>
      </div>

      <div className="start-over-row">
        <button className="btn-secondary" onClick={onReset}>← Start Over</button>
      </div>
    </div>
  )
}
