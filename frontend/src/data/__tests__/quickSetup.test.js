import { test, expect } from 'vitest'
import { FIXED_QUESTIONS } from '../quickSetup'

test('every fixed option includes dropdown technical_effect data', () => {
  for (const q of FIXED_QUESTIONS) {
    expect(q.id).toBeTruthy()
    expect(q.question).toBeTruthy()
    expect(Array.isArray(q.options)).toBe(true)
    expect(q.options.length).toBeGreaterThan(0)
    for (const opt of q.options) {
      expect(opt.label).toBeTruthy()
      expect(opt.value).toBeTruthy()
      expect(opt.technical_effect).toBeTruthy()
      expect(typeof opt.technical_effect.explanation).toBe('string')
      expect(opt.technical_effect.explanation.length).toBeGreaterThan(0)
      expect(Array.isArray(opt.technical_effect.constraint_impacts)).toBe(true)
      expect(opt.technical_effect.constraint_impacts.length).toBeGreaterThan(0)
    }
  }
})

