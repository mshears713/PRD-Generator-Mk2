import { useEffect, useState } from 'react'
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
const API_BASE = import.meta.env.VITE_API_URL || window.location.origin
console.log('API_BASE:', API_BASE)

const FALLBACK_RECOMMENDATION = {
  summary: 'No recommendation data yet. Choose your stack below and generate when ready.',
  selections: { scope: 'fullstack', backend: 'fastapi', frontend: 'react', apis: [], database: 'postgres', api_keys: {} },
  deployment: 'self',
}

export default function App() {
  const [activeTab, setActiveTab] = useState('current')
  const [stage, setStage] = useState('recommendation')
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
  const [deployment, setDeployment] = useState('')
  const [output, setOutput] = useState(null)
  const [error, setError] = useState('')
  const [loadingLatest, setLoadingLatest] = useState(true)
  const [sessionId, setSessionId] = useState('')
  const [iterating, setIterating] = useState(false)
  const [iterateError, setIterateError] = useState('')
  const [sessionsList, setSessionsList] = useState([])
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [sessionsError, setSessionsError] = useState('')

  function applyRecommendationData(data) {
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
    setSelections({
      scope: data.recommended?.scope || '',
      backend: data.recommended?.backend || '',
      frontend: data.recommended?.frontend || '',
      apis: data.recommended?.apis || [],
      database: data.recommended?.database || '',
      api_keys: {},
    })
    const recommendedDeployment = depOpts.find(opt => opt.recommended)?.value || ''
    setDeployment(recommendedDeployment)
    setStage('recommendation')
  }

  useEffect(() => {
    async function loadLatestSession() {
      setError('')
      setLoadingLatest(true)
      try {
        const res = await fetch(`${API_BASE}/sessions/latest`)
        if (!res.ok) throw new Error('Failed to load latest session')
        const data = await res.json()
        const session = data.session
        if (session?.recommendation) {
          setSessionId(session.id || '')
          setIdea(session.idea || '')
          applyRecommendationData(session.recommendation)
        }
      } catch (e) {
        setError(e.message)
      } finally {
        setLoadingLatest(false)
      }
    }
    loadLatestSession()
  }, [])

  useEffect(() => {
    if (activeTab !== 'previous') return
    async function loadSessionsList() {
      setLoadingSessions(true)
      setSessionsError('')
      try {
        const res = await fetch(`${API_BASE}/sessions`)
        if (!res.ok) throw new Error('Failed to load sessions')
        const data = await res.json()
        setSessionsList(data.sessions || [])
      } catch (e) {
        setSessionsError(e.message)
      } finally {
        setLoadingSessions(false)
      }
    }
    loadSessionsList()
  }, [activeTab])

  async function handleQuickSetupContinue(answers) {
    setStage('recommending')
    setError('')
    try {
      const res = await fetch(`${API_BASE}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, answers }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      const data = await res.json()
      applyRecommendationData(data)
      try {
        const latestRes = await fetch(`${API_BASE}/sessions/latest`)
        if (latestRes.ok) {
          const latestData = await latestRes.json()
          setSessionId(latestData?.session?.id || '')
        }
      } catch (_) {
        // Ignore session id refresh failure; recommendation still loaded.
      }
    } catch (e) {
      setError(e.message)
      setStage('quicksetup')
    }
  }

  async function handleIterateRecommendation(feedback) {
    const cleanFeedback = (feedback || '').trim()
    if (!cleanFeedback) {
      setIterateError('Feedback is required.')
      return false
    }
    if (!sessionId) {
      setIterateError('No session loaded yet.')
      return false
    }
    setIterateError('')
    setIterating(true)
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}/iterate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback: cleanFeedback }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed to update recommendation')
      const data = await res.json()
      applyRecommendationData(data)
      return true
    } catch (e) {
      setIterateError(e.message)
      return false
    } finally {
      setIterating(false)
    }
  }

  async function handleLoadSession(sessionToLoadId) {
    setError('')
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionToLoadId}`)
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed to load session')
      const data = await res.json()
      const session = data.session
      setSessionId(session.id || '')
      setIdea(session.idea || '')
      applyRecommendationData(session.recommendation || {})
      setActiveTab('current')
    } catch (e) {
      setError(e.message)
    }
  }

  function formatSessionDate(value) {
    if (!value) return 'Unknown date'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleString()
  }

  function summarizeIdea(text) {
    const clean = (text || '').trim()
    if (!clean) return 'Untitled project'
    if (clean.length <= 90) return clean
    return `${clean.slice(0, 90)}...`
  }

  async function handleGenerate() {
    setStage('generating')
    setError('')
    try {
      const body = {
        idea: String(idea),
        scope: selections.scope,
        backend: selections.backend,
        frontend: selections.frontend,
        apis: selections.apis || [],
        database: selections.database,
        api_keys: selections.api_keys || {},
      }
      console.log('Generate request body:', body)
      const res = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
    setStage('recommendation')
    setIdea('')
    setSummary(FALLBACK_RECOMMENDATION.summary)
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
    setDeployment('')
    setOutput(null)
    setError('')
    setSessionId('')
    setIterateError('')
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

      <div className="mb-6 flex gap-2">
        <button
          type="button"
          className={`px-3 py-1.5 rounded-md text-sm border ${activeTab === 'current' ? 'bg-accent/15 border-accent text-foreground' : 'border-border text-muted'}`}
          onClick={() => setActiveTab('current')}
        >
          Current Project
        </button>
        <button
          type="button"
          className={`px-3 py-1.5 rounded-md text-sm border ${activeTab === 'previous' ? 'bg-accent/15 border-accent text-foreground' : 'border-border text-muted'}`}
          onClick={() => setActiveTab('previous')}
        >
          Previous Projects
        </button>
      </div>

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

      {activeTab === 'current' && loadingLatest && (
        <LoadingState message="Loading latest recommendation..." />
      )}
      {activeTab === 'current' && !loadingLatest && stage === 'idea' && (
        <IdeaInput idea={idea} onChange={setIdea} onSubmit={() => setStage('quicksetup')} />
      )}
      {activeTab === 'current' && !loadingLatest && stage === 'quicksetup' && (
        <QuickSetupPanel idea={idea} onContinue={handleQuickSetupContinue} apiBase={API_BASE} />
      )}
      {activeTab === 'current' && !loadingLatest && stage === 'recommending' && (
        <LoadingState message="Analyzing your idea..." />
      )}
      {activeTab === 'current' && !loadingLatest && stage === 'recommendation' && (
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
          sessionId={sessionId}
          onIterate={handleIterateRecommendation}
          iterating={iterating}
          iterateError={iterateError}
        />
      )}
      {activeTab === 'current' && stage === 'generating' && (
        <LoadingState stages={GENERATE_STAGES} cycleInterval={6000} />
      )}
      {activeTab === 'current' && stage === 'output' && (
        <OutputPanel output={output} idea={idea} onReset={handleReset} apiBase={API_BASE} />
      )}

      {activeTab === 'previous' && (
        <div className="flex flex-col gap-3">
          {loadingSessions && <p className="text-sm text-muted">Loading previous projects...</p>}
          {sessionsError && <p className="text-sm text-danger">{sessionsError}</p>}
          {!loadingSessions && !sessionsError && sessionsList.length === 0 && (
            <p className="text-sm text-muted">No previous projects yet.</p>
          )}
          {!loadingSessions && sessionsList.map(session => (
            <button
              key={session.id}
              type="button"
              className="text-left border border-border rounded-lg p-4 hover:border-accent/60 transition"
              onClick={() => handleLoadSession(session.id)}
            >
              <p className="text-sm font-semibold text-foreground">{summarizeIdea(session.idea)}</p>
              <p className="text-xs text-muted mt-1">Created: {formatSessionDate(session.created_at)}</p>
              {session.updated_at && (
                <p className="text-xs text-muted">Updated: {formatSessionDate(session.updated_at)}</p>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
