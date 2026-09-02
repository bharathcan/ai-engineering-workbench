import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import '@testing-library/jest-dom/vitest'

// RTL's automatic afterEach cleanup only self-registers when it detects a
// global `afterEach` — this project deliberately does not set vitest's
// `test.globals: true` (see vite.config.ts), so it has to be wired up
// explicitly here, or renders from one test leak into the next.
afterEach(() => {
  cleanup()
})
