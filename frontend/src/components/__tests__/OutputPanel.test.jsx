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

  render(<OutputPanel output={output} idea="Foo" onReset={() => {}} />)

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

  render(<OutputPanel output={output} idea="Foo" onReset={() => {}} />)

  expect(screen.getByText('Main PRD')).toBeInTheDocument()
  expect(screen.getByText('Backend PRD')).toBeInTheDocument()
  expect(screen.queryByText('Frontend PRD')).toBeNull()
})


test('create repo success shows repo link and kickoff prompt', async () => {
  const output = {
    main_prd: '# Foo PRD\n\n## Overview\nMain doc.',
    backend_prd: '# Foo Backend PRD\n\n## Purpose\nBackend doc.',
    env: 'OPENAI_API_KEY=sk-test',
    growth_check: { good: [], warnings: [], missing: [] },
  }

  global.fetch = async () => ({
    ok: true,
    json: async () => ({
      repo_name: 'foo',
      repo_url: 'https://github.com/me/foo',
      kickoff_prompt: 'Do the thing',
      created_files: ['README.md'],
    }),
  })

  render(<OutputPanel output={output} idea="Foo" onReset={() => {}} />)

  fireEvent.click(screen.getByText('Create GitHub Repo'))
  expect(await screen.findByText('https://github.com/me/foo')).toBeInTheDocument()
  expect(await screen.findByText('Do the thing')).toBeInTheDocument()
})


test('create repo error shows message without breaking PRDs', async () => {
  const output = {
    main_prd: '# Foo PRD\n\n## Overview\nMain doc.',
    backend_prd: '# Foo Backend PRD\n\n## Purpose\nBackend doc.',
    env: '',
    growth_check: { good: [], warnings: [], missing: [] },
  }

  global.fetch = async () => ({
    ok: false,
    json: async () => ({ detail: 'GITHUB_TOKEN not set. Set it to use Create GitHub Repo.' }),
  })

  render(<OutputPanel output={output} idea="Foo" onReset={() => {}} />)

  fireEvent.click(screen.getByText('Create GitHub Repo'))
  expect(await screen.findByText('GITHUB_TOKEN not set. Set it to use Create GitHub Repo.')).toBeInTheDocument()
  expect(screen.getByText('Main PRD')).toBeInTheDocument()
  expect(screen.getByText('Backend PRD')).toBeInTheDocument()
})
