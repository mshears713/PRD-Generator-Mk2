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

export default function OutputPanel({ output, onReset }) {
  return (
    <div className="output-stage">
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

      <div className="output-section">
        <h2 className="output-section-title">Growth Check</h2>
        <div className="markdown-body">
          <ReactMarkdown>{output.growth_check}</ReactMarkdown>
        </div>
      </div>

      <div className="start-over-row">
        <button className="btn-secondary" onClick={onReset}>← Start Over</button>
      </div>
    </div>
  )
}
