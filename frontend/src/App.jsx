import { useState } from 'react'
import { Alert } from '@heroui/react'
import IdeaInput from './components/IdeaInput'
import LoadingState from './components/LoadingState'
import QuickSetupPanel from './components/QuickSetupPanel'
import RecommendationPanel from './components/RecommendationPanel'
import OutputPanel from './components/OutputPanel'
import './styles/globals.css'

const GENERATE_STAGES = [
  'Normalizing system definition...',
  'Analyzing architecture...',
  'Generating PRDs...',
  'Running System Review...',
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
  const [apiCandidates, setApiCandidates] = useState(null)
  const [deploymentOptions, setDeploymentOptions] = useState([])
  const [selections, setSelections] = useState({
    scope: '', backend: '', frontend: '', apis: [], database: '', api_keys: {},
  })
  const [deployment, setDeployment] = useState('self')
  const [output, setOutput] = useState(null)
  const [error, setError] = useState('')

  function handleUnderstand() {
    if (!idea.trim()) return
    setError('')
    setStage('quicksetup')
  }

  async function handleQuickSetupContinue(answers) {
    setStage('recommending')
    setError('')
    try {
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, answers }),
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
      setApiCandidates(data.api_candidates || null)
      const depOpts = data.deployment || []
      setDeploymentOptions(depOpts)
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
    setApiCandidates(null)
    setDeploymentOptions([])
    setSelections({ scope: '', backend: '', frontend: '', apis: [], database: '', api_keys: {} })
    setDeployment('self')
    setOutput(null)
    setError('')
  }

  return (
    <div className="max-w-[1100px] mx-auto px-6 py-8 pb-16">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold flex items-center justify-center gap-2">
          <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            className="w-7 h-7 text-accent"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3.5-3.5" />
          </svg>
          <span className="bg-gradient-to-br from-accent to-violet-400 bg-clip-text text-transparent">
            StackLens
          </span>
        </h1>
        <p className="text-muted mt-1 text-base">From idea → architecture in minutes</p>
      </header>

      {error && (
        <div className="mb-6">
          <Alert status="danger">
            <Alert.Indicator />
            <Alert.Content>
              <Alert.Description>{error}</Alert.Description>
            </Alert.Content>
          </Alert>
        </div>
      )}

      {stage === 'idea' && (
        <IdeaInput idea={idea} onChange={setIdea} onSubmit={handleUnderstand} />
      )}
      {stage === 'quicksetup' && (
        <QuickSetupPanel idea={idea} onContinue={handleQuickSetupContinue} />
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
          apiCandidates={apiCandidates}
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
        <OutputPanel output={output} idea={idea} onReset={handleReset} />
      )}
    </div>
  )
}
