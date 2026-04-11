import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { test, expect, vi } from 'vitest'
import QuickSetupPanel from '../QuickSetupPanel'

const dynamicQuestions = [
  {
    id: 'output_type',
    question: 'What should it produce at the end?',
    options: [
      {
        label: 'An answer on the screen',
        value: 'onscreen',
        technical_effect: {
          explanation: 'Optimizes for fast request/response output.',
          constraint_impacts: ['Sets derived.output_type = onscreen'],
        },
      },
      {
        label: 'A downloadable file',
        value: 'file_export',
        technical_effect: {
          explanation: 'Adds file generation concerns.',
          constraint_impacts: ['Sets derived.output_type = file_export'],
        },
      },
    ],
  },
  {
    id: 'automation_level',
    question: 'How automated should it be?',
    options: [
      {
        label: 'Only when I click',
        value: 'manual',
        technical_effect: {
          explanation: 'Keeps execution user-driven.',
          constraint_impacts: ['Sets derived.automation_level = manual'],
        },
      },
      {
        label: 'Run on a schedule',
        value: 'scheduled',
        technical_effect: {
          explanation: 'Introduces background execution.',
          constraint_impacts: ['Sets derived.automation_level = scheduled'],
        },
      },
    ],
  },
]

test('renders fixed + dynamic questions and continues with structured answers', async () => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ questions: dynamicQuestions }),
  })

  const onContinue = vi.fn()
  render(<QuickSetupPanel idea="A report exporter" onContinue={onContinue} />)

  expect(screen.getByText('Quick Setup')).toBeInTheDocument()
  expect(screen.getByText('Who is this for?')).toBeInTheDocument()

  await screen.findByText('What should it produce at the end?')

  fireEvent.click(screen.getByText('Public'))
  fireEvent.click(screen.getByText('A downloadable file'))

  const explain = screen.getAllByText(/What does this choice change/i)[0]
  fireEvent.click(explain)
  expect(screen.getByText(/Sets user_scale/i)).toBeInTheDocument()

  fireEvent.click(screen.getByText(/Continue/i))

  expect(onContinue).toHaveBeenCalledTimes(1)
  const payload = onContinue.mock.calls[0][0]
  expect(payload.fixed_answers).toBeTruthy()
  expect(payload.dynamic_answers).toBeTruthy()
  expect(payload.fixed_answers.for_whom).toBe('large')
  expect(payload.dynamic_answers.output_type).toBe('file_export')

  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalled()
  })
})
