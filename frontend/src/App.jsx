import { useState } from 'react'
import IdeaInput from './components/IdeaInput'
import LoadingState from './components/LoadingState'
import './styles/main.css'

const GENERATE_STAGES = [
  'Normalizing system definition...',
  'Analyzing architecture...',
  'Generating PRD...',
  'Running Growth Check...',
]

export default function App() {
  const [stage, setStage] = useState('idea')
  const [idea, setIdea] = useState('')
  const [summary, setSummary] = useState('')
  const [recommended, setRecommended] = useState(null)
  const [selections, setSelections] = useState({
    scope: '', backend: '', frontend: '', apis: [], database: '', api_keys: {},
  })
  const [output, setOutput] = useState(null)
  const [error, setError] = useState('')

  async function handleUnderstand() {
    if (!idea.trim()) return
    setStage('recommending')
    setError('')
    try {
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      const data = await res.json()
      setSummary(data.summary)
      setRecommended(data.recommended)
      setSelections({ ...data.recommended, api_keys: {} })
      setStage('recommendation')
    } catch (e) {
      setError(e.message)
      setStage('idea')
    }
  }

  async function handleGenerate() {
    setStage('generating')
    setError('')
    try {
      const res = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, ...selections }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      const data = await res.json()
      setOutput(data)
      setStage('output')
    } catch (e) {
      setError(e.message)
      setStage('recommendation')
    }
  }

  function handleReset() {
    setStage('idea')
    setIdea('')
    setSummary('')
    setRecommended(null)
    setSelections({ scope: '', backend: '', frontend: '', apis: [], database: '', api_keys: {} })
    setOutput(null)
    setError('')
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>CodeGarden</h1>
        <p className="app-tagline">Grow your idea into a build-ready blueprint</p>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {stage === 'idea' && (
        <IdeaInput idea={idea} onChange={setIdea} onSubmit={handleUnderstand} />
      )}
      {stage === 'recommending' && (
        <LoadingState message="Understanding your idea..." />
      )}
      {stage === 'generating' && (
        <LoadingState stages={GENERATE_STAGES} cycleInterval={6000} />
      )}
    </div>
  )
}
