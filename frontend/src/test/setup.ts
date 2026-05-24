import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { cleanup } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { handlers } from './mswHandlers'
import { client } from '@/client/client.gen'

// jsdom + undici require absolute URLs; the SDK defaults to relative paths in the
// browser (the Vite dev proxy handles routing). Point it at a deterministic host
// so MSW can intercept.
client.setConfig({ baseUrl: 'http://localhost' })

export const server = setupServer(...handlers)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
  localStorage.clear()
})
afterAll(() => server.close())
