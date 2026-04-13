import React, { useEffect, useMemo, useState } from 'react'
import { Button, ToggleButton, ToggleButtonGroup } from '@heroui/react'
import { DEFAULT_FIXED_ANSWERS, FIXED_QUESTIONS } from '../data/quickSetup'

function ExplainDropdown({ option }) {
  if (!option) return null
  const explanation = option.technical_effect?.explanation
  const impacts = option.technical_effect?.constraint_impacts || []

  if (!explanation && impacts.length === 0) return null

  return (
    <details className="mt-3 rounded-md border border-border bg-surface/40 px-3 py-2">
      <summary className="cursor-pointer text-sm text-muted select-none">
        What does this choice change?
      </summary>
      <div className="mt-2 text-sm text-foreground">
        {explanation && <p className="leading-relaxed">{explanation}</p>}
        {impacts.length > 0 && (
          <ul className="mt-2 flex flex-col gap-1">
            {impacts.map((line, i) => (
              <li key={i} className="text-muted pl-3 relative before:content-['•'] before:absolute before:left-0 before:text-accent">
                {line}
              </li>
            ))}
          </ul>
        )}
      </div>
    </details>
  )
}

function QuestionBlock({ question, value, onChange }) {
  const selectedOption = useMemo(
    () => question.options.find(o => o.value === value),
    [question.options, value],
  )

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">{question.question}</p>
      <ToggleButtonGroup
        selectionMode="single"
        selectedKeys={new Set([value])}
        onSelectionChange={keys => {
          const v = [...keys][0]
          if (v) onChange(v)
        }}
        size="sm"
        className="flex-wrap"
      >
        {question.options.map((opt, idx) => (
          <React.Fragment key={opt.value}>
            {idx > 0 && <ToggleButtonGroup.Separator />}
            <ToggleButton id={opt.value}>{opt.label}</ToggleButton>
          </React.Fragment>
        ))}
      </ToggleButtonGroup>
      <ExplainDropdown option={selectedOption} />
    </div>
  )
}

export default function QuickSetupPanel({ idea, onContinue, apiBase = window.location.origin }) {
  const [fixedAnswers, setFixedAnswers] = useState(DEFAULT_FIXED_ANSWERS)
  const [dynamicQuestions, setDynamicQuestions] = useState([])
  const [dynamicAnswers, setDynamicAnswers] = useState({})
  const [dynamicLoading, setDynamicLoading] = useState(false)
  const [dynamicError, setDynamicError] = useState('')

  function mapFixedAnswersForBackend(answers) {
    const next = { ...(answers || {}) }
    const scale = next.for_whom
    if (scale === 'scale_1') next.for_whom = 'single'
    else if (scale === 'scale_10' || scale === 'scale_100') next.for_whom = 'small'
    else if (scale === 'scale_1000' || scale === 'scale_1000_plus') next.for_whom = 'large'
    return next
  }

  async function loadDynamicQuestions() {
    if (!idea?.trim()) return
    setDynamicLoading(true)
    setDynamicError('')
    try {
      const res = await fetch(`${apiBase}/quick-setup/questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed to load questions')
      const data = await res.json()
      setDynamicQuestions(data.questions || [])
    } catch (e) {
      setDynamicQuestions([])
      setDynamicError(e.message)
    } finally {
      setDynamicLoading(false)
    }
  }

  useEffect(() => {
    loadDynamicQuestions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idea])

  useEffect(() => {
    setDynamicAnswers(prev => {
      const next = { ...prev }
      for (const q of dynamicQuestions) {
        const existing = next[q.id]
        const stillValid = q.options?.some(o => o.value === existing)
        if (stillValid) continue
        const first = q.options?.[0]?.value
        if (first) next[q.id] = first
      }
      return next
    })
  }, [dynamicQuestions])

  return (
    <div className="flex flex-col gap-6 max-w-[760px] mx-auto w-full">
      <div className="text-center">
        <p className="font-semibold text-foreground">Quick Setup</p>
        <p className="text-muted text-sm mt-1">6 questions · ~20 seconds</p>
      </div>

      <div className="flex flex-col gap-4">
        {FIXED_QUESTIONS.map(q => (
          <QuestionBlock
            key={q.id}
            question={q}
            value={fixedAnswers[q.id]}
            onChange={v => setFixedAnswers(prev => ({ ...prev, [q.id]: v }))}
          />
        ))}

        <div className="pt-2">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-2">Idea-based questions</p>
          {dynamicLoading && (
            <p className="text-muted text-sm">Loading questions…</p>
          )}
          {dynamicError && (
            <div className="flex items-center gap-3 flex-wrap">
              <p className="text-muted text-sm">Couldn’t load idea-based questions.</p>
              <Button size="sm" variant="flat" onPress={loadDynamicQuestions}>
                Retry
              </Button>
            </div>
          )}
        </div>

        {dynamicQuestions.map(q => (
          <QuestionBlock
            key={q.id}
            question={q}
            value={dynamicAnswers[q.id]}
            onChange={v => setDynamicAnswers(prev => ({ ...prev, [q.id]: v }))}
          />
        ))}
      </div>

      <Button
        variant="primary"
        className="w-full"
        onPress={() => onContinue({ fixed_answers: mapFixedAnswersForBackend(fixedAnswers), dynamic_answers: dynamicAnswers })}
      >
        Continue →
      </Button>
    </div>
  )
}
