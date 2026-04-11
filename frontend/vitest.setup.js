import { expect as vitestExpect } from 'vitest'
import * as matchers from '@testing-library/jest-dom/matchers'
import React from 'react'

const activeExpect = globalThis.expect ?? vitestExpect
if (activeExpect?.extend) {
  activeExpect.extend(matchers)
}

// Ensure React is available for components compiled with classic runtime
globalThis.React = React
