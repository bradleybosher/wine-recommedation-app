import { act, render } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'

import { RecommendationProvider, useRecommendations } from '@/state/recommendationStore'
import type { RecommendationResponse } from '@/client/types.gen'

describe('RecommendationProvider', () => {
  it('keeps a stable context value across unrelated parent re-renders', () => {
    const seen: unknown[] = []
    let bump: () => void = () => {}

    function Consumer() {
      const ctx = useRecommendations()
      seen.push(ctx)
      return null
    }

    function Parent() {
      const [, setN] = useState(0)
      bump = () => setN((n) => n + 1)
      return (
        <RecommendationProvider>
          <Consumer />
        </RecommendationProvider>
      )
    }

    render(<Parent />)
    // Re-render the parent without changing recommendations.
    act(() => bump())

    expect(seen.length).toBeGreaterThanOrEqual(2)
    // Memoized value object keeps the same reference when state is unchanged.
    expect(seen[seen.length - 1]).toBe(seen[0])
  })

  it('updates the context value when recommendations change', () => {
    const values: Array<ReturnType<typeof useRecommendations>> = []

    function Consumer() {
      const ctx = useRecommendations()
      values.push(ctx)
      return null
    }

    render(
      <RecommendationProvider>
        <Consumer />
      </RecommendationProvider>,
    )

    const sample = { recommendations: [] } as unknown as RecommendationResponse
    act(() => values[values.length - 1].setRecommendations(sample))

    const latest = values[values.length - 1]
    expect(latest.recommendations).toBe(sample)
    // New reference once the underlying state actually changes.
    expect(latest).not.toBe(values[0])
  })
})
