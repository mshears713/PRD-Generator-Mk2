import { useState } from 'react'
import IdeaInput from './components/IdeaInput'
import LoadingState from './components/LoadingState'
import QuickSetupPanel from './components/QuickSetupPanel'
import RecommendationPanel from './components/RecommendationPanel'
import OutputPanel from './components/OutputPanel'
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
  const [systemType, setSystemType] = useState('')
  const [keyRequirements, setKeyRequirements] = useState([])
  const [rationale, setRationale] = useState(null)
  const [coreSystemLogic, setCoreSystemLogic] = useState('')
  const [scopeBoundaries, setScopeBoundaries] = useState([])
  const [phasedPlan, setPhasedPlan] = useState([])
  const [architectureData, setArchitectureData] = useState(null)
  const [deploymentOptions, setDeploymentOptions] = useState([])
  const [selections, setSelections] = useState({
    scope: '', backend: '', frontend: '', apis: [], database: '', api_keys: {},
  })
  const [deployment, setDeployment] = useState('render')
  const [output, setOutput] = useState(null)
  const [error, setError] = useState('')

  function handleUnderstand() {
    if (!idea.trim()) return
    setError('')
    setStage('quicksetup')
  }

  async function handleQuickSetupContinue(constraints) {
    setStage('recommending')
    setError('')
    try {
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, constraints }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      const data = await res.json()
      setSummary(data.system_understanding || data.summary || '')
      setSystemType(data.system_type || '')
      setKeyRequirements(data.key_requirements || [])
      setRationale(data.rationale || null)
      setCoreSystemLogic(data.core_system_logic || '')
      setScopeBoundaries(data.scope_boundaries || [])
      setPhasedPlan(data.phased_plan || [])
      setArchitectureData(data.architecture || null)
      const depOpts = data.deployment || []
      setDeploymentOptions(depOpts)
      const recommended = depOpts.find(d => d.recommended)
      if (recommended) setDeployment(recommended.value)
      setSelections({ ...data.recommended, api_keys: {} })
      setStage('recommendation')
    } catch (e) {
      setError(e.message)
      setStage('quicksetup')
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
    setSystemType('')
    setKeyRequirements([])
    setRationale(null)
    setCoreSystemLogic('')
    setScopeBoundaries([])
    setPhasedPlan([])
    setArchitectureData(null)
    setDeploymentOptions([])
    setSelections({ scope: '', backend: '', frontend: '', apis: [], database: '', api_keys: {} })
    setDeployment('render')
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
      {stage === 'quicksetup' && (
        <QuickSetupPanel onContinue={handleQuickSetupContinue} />
      )}
      {stage === 'recommending' && (
        <LoadingState message="Analyzing your idea..." />
      )}
      {stage === 'recommendation' && (
        <RecommendationPanel
          summary={summary}
          systemType={systemType}
          keyRequirements={keyRequirements}
          rationale={rationale}
          coreSystemLogic={coreSystemLogic}
          scopeBoundaries={scopeBoundaries}
          phasedPlan={phasedPlan}
          selections={selections}
          onChange={setSelections}
          architectureData={architectureData}
          deployment={deployment}
          onDeploymentChange={setDeployment}
          deploymentOptions={deploymentOptions}
          onGenerate={handleGenerate}
        />
      )}
      {stage === 'generating' && (
        <LoadingState stages={GENERATE_STAGES} cycleInterval={6000} />
      )}
      {stage === 'output' && (
        <OutputPanel output={output} onReset={handleReset} />
      )}
    </div>
  )
}
