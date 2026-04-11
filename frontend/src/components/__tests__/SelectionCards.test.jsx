import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import SelectionCards from '../SelectionCards'

const apiCandidates = {
  selected: [
    {
      id: 'upstash_redis',
      name: 'Upstash Redis',
      category: 'database',
      status: 'selected',
      recommended: true,
      reason: 'Cache helpful',
      sponsored: true,
      sponsor_note: 'Sponsored option: sign up bonus / builder credit messaging',
      best_for: ['cache'],
      avoid_when: ['relational schema'],
    },
  ],
  candidates: [
    {
      id: 'tavily',
      name: 'Tavily',
      category: 'research_search',
      status: 'candidate',
      recommended: false,
      reason: 'Search may help',
      sponsored: false,
      best_for: ['web search'],
      avoid_when: [],
    },
  ],
  rejected: [
    {
      id: 'blaxel',
      name: 'Blaxel',
      category: 'testing',
      status: 'rejected',
      why_not: 'testing=false',
      sponsored: false,
    },
  ],
}

const selections = {
  scope: 'fullstack',
  backend: 'fastapi',
  frontend: 'react',
  database: 'postgres',
  apis: ['upstash_redis'],
  api_keys: {},
}

const noop = vi.fn()

test('shows sponsored badge for Upstash Redis and rejected chip', () => {
  render(
    <SelectionCards
      selections={selections}
      onChange={noop}
      architectureData={null}
      apiCandidates={apiCandidates}
    />
  )

  expect(screen.getAllByText('Upstash Redis').length).toBeGreaterThan(0)
  expect(screen.getAllByText(/Sponsored/).length).toBeGreaterThan(0)
  expect(screen.getByText(/Blaxel/)).toBeInTheDocument()
})
