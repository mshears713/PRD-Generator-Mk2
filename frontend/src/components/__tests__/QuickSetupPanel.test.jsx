import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import QuickSetupPanel from '../QuickSetupPanel'

test('renders testing toggle defaulting to no', () => {
  const onContinue = vi.fn()
  render(<QuickSetupPanel onContinue={onContinue} />)
  expect(screen.getByText(/Include testing support/i)).toBeInTheDocument()
  const noButton = screen.getAllByRole('radio', { name: /Not now/i })[0]
  expect(noButton.getAttribute('aria-checked')).toBe('true')
})

test('sets testing true when Yes selected', async () => {
  const onContinue = vi.fn()
  render(<QuickSetupPanel onContinue={onContinue} />)
  const yesButton = screen.getAllByRole('radio', { name: /Yes, include testing/i })[0]
  fireEvent.click(yesButton)
  expect(yesButton.getAttribute('aria-checked')).toBe('true')
})
