import React from 'react'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { test, expect, afterEach } from 'vitest'
import OutputPanel from '../OutputPanel'

afterEach(() => cleanup())


test('renders segmented control and switches between PRDs when all docs present', () => {
  const output = {
    main_prd: '# Foo PRD\n\n## Overview\nMain doc.',
    backend_prd: '# Foo Backend PRD\n\n## Purpose\nBackend doc.',
    frontend_prd: '# Foo Frontend PRD\n\n## Purpose\nFrontend doc.',
    env: '',
    growth_check: { good: [], warnings: [], missing: [] },
  }

  render(<OutputPanel output={output} onReset={() => {}} />)

  expect(screen.getByText('Main PRD')).toBeInTheDocument()
  expect(screen.getByText('Backend PRD')).toBeInTheDocument()
  expect(screen.getByText('Frontend PRD')).toBeInTheDocument()

  expect(screen.getByText('Foo PRD')).toBeInTheDocument()

  fireEvent.click(screen.getByText('Backend PRD'))
  expect(screen.getByText('Foo Backend PRD')).toBeInTheDocument()

  fireEvent.click(screen.getByText('Frontend PRD'))
  expect(screen.getByText('Foo Frontend PRD')).toBeInTheDocument()
})


test('omits frontend option when frontend_prd is absent', () => {
  const output = {
    main_prd: '# Foo PRD\n\n## Overview\nMain doc.',
    backend_prd: '# Foo Backend PRD\n\n## Purpose\nBackend doc.',
    env: '',
    growth_check: { good: [], warnings: [], missing: [] },
  }

  render(<OutputPanel output={output} onReset={() => {}} />)

  expect(screen.getByText('Main PRD')).toBeInTheDocument()
  expect(screen.getByText('Backend PRD')).toBeInTheDocument()
  expect(screen.queryByText('Frontend PRD')).toBeNull()
})
