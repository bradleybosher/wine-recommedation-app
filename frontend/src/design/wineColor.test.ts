import { describe, expect, it } from 'vitest'

import { DEFAULT_PALETTE, PALETTES } from '@/design/tokens'
import { derivePalette, enrichWine } from '@/design/wineColor'
import type { WineRecommendation } from '@/client/types.gen'

describe('derivePalette', () => {
  it('returns brunello palette for sangiovese keywords', () => {
    expect(derivePalette('Sangiovese', 'Tuscany')).toBe(PALETTES.brunello)
    expect(derivePalette(null, 'Brunello di Montalcino')).toBe(PALETTES.brunello)
  })

  it('returns barolo palette for nebbiolo keywords', () => {
    expect(derivePalette('Nebbiolo', 'Piedmont')).toBe(PALETTES.barolo)
    expect(derivePalette(null, 'Barolo')).toBe(PALETTES.barolo)
  })

  it('returns chablis palette for white-wine keywords', () => {
    expect(derivePalette('Chardonnay', null)).toBe(PALETTES.chablis)
    expect(derivePalette('Riesling', 'Mosel')).toBe(PALETTES.chablis)
  })

  it('returns rose palette for rosé keywords', () => {
    expect(derivePalette(null, 'Provence rosé')).toBe(PALETTES.rose)
  })

  it('returns default palette for unknown varietal+region', () => {
    expect(derivePalette('Mystery Grape', 'Unknown Region')).toBe(DEFAULT_PALETTE)
  })

  it('handles null inputs without throwing', () => {
    expect(derivePalette(null, null)).toBe(DEFAULT_PALETTE)
    expect(derivePalette(undefined, undefined)).toBe(DEFAULT_PALETTE)
  })
})

describe('enrichWine', () => {
  const baseWine: WineRecommendation = {
    rank: 1,
    wineName: 'Test Wine',
    grape: null,
    region: 'Burgundy',
    appellation: null,
    vintage: 2018,
    reasoning: 'Bright and elegant. Long finish.',
    confidence: 'medium',
  } as WineRecommendation

  it('derives country from region when not provided', () => {
    expect(enrichWine(baseWine).country).toBe('France')
  })

  it('derives bars when backend omits them', () => {
    const enriched = enrichWine({ ...baseWine, grape: 'Nebbiolo' })
    expect(enriched.bars.tannin).toBeGreaterThan(7)
    expect(enriched.bars.acidity).toBeGreaterThan(7)
  })

  it('preserves backend-provided bars verbatim', () => {
    const provided = { tannin: 5, acidity: 5, body: 5, sweetness: 5, oak: 5 }
    const enriched = enrichWine({ ...baseWine, bars: provided } as WineRecommendation)
    expect(enriched.bars).toEqual(provided)
  })

  it('falls back to derived coords for unknown regions', () => {
    const enriched = enrichWine({ ...baseWine, region: 'Made-Up Land' })
    expect(typeof enriched.coords.lat).toBe('number')
    expect(typeof enriched.coords.lon).toBe('number')
  })

  it('extracts nose from first sentence when nose absent', () => {
    const enriched = enrichWine(baseWine)
    expect(enriched.nose).toContain('bright')
  })

  it('keeps drink window vintage-relative when not provided', () => {
    const enriched = enrichWine({ ...baseWine, vintage: 2015 })
    expect(enriched.drink.from).toBeGreaterThanOrEqual(2015)
    expect(enriched.drink.until).toBeGreaterThan(enriched.drink.peak)
    expect(enriched.drink.peak).toBeGreaterThan(enriched.drink.from)
  })
})
