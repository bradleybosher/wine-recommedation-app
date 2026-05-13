import type { WineRecommendation } from '@/client/types.gen';
import { DEFAULT_PALETTE, PALETTES, type WinePalette } from '@/design/tokens';

export interface WineBars {
  tannin: number;
  acidity: number;
  body: number;
  sweetness: number;
  oak: number;
}

export interface DrinkWindow {
  from: number;
  peak: number;
  until: number;
}

export interface WineCritic {
  score: number;
  source: string;
}

export interface WineCoords {
  lat: number;
  lon: number;
}

// Full enriched wine record used across all Phase 3 screens.
// Phase 5 will replace derived fields with real backend data.
export interface EnrichedWine extends WineRecommendation {
  id: string;
  name: string;
  country: string;
  appellation: string;
  coords: WineCoords;
  grape: string;
  abv: number;
  drink: DrinkWindow;
  color: WinePalette;
  bars: WineBars;
  wheel: Record<string, number>;
  nose: string;
  palate: string;
  fits: string[];
  pairs: string[];
  critic: WineCritic;
}

function matchKeywords(text: string, keywords: string[]): boolean {
  const lower = text.toLowerCase();
  return keywords.some((k) => lower.includes(k));
}

export function derivePalette(
  varietal?: string | null,
  region?: string | null,
): WinePalette {
  const source = `${varietal ?? ''} ${region ?? ''}`;
  if (matchKeywords(source, ['sangiovese', 'brunello', 'chianti', 'montalcino'])) {
    return PALETTES.brunello;
  }
  if (matchKeywords(source, ['nebbiolo', 'barolo', 'barbaresco', 'piedmont', 'piemonte'])) {
    return PALETTES.barolo;
  }
  if (matchKeywords(source, ['chardonnay', 'chablis', 'burgundy', 'bourgogne', 'white'])) {
    return PALETTES.chablis;
  }
  if (matchKeywords(source, ['pinot noir', 'burgundy', 'bourgogne'])) {
    return PALETTES.chablis;
  }
  return DEFAULT_PALETTE;
}

function deriveBars(varietal?: string | null, region?: string | null): WineBars {
  const source = `${varietal ?? ''} ${region ?? ''}`;
  if (matchKeywords(source, ['nebbiolo', 'barolo', 'barbaresco'])) {
    return { tannin: 9, acidity: 8, body: 7, sweetness: 1, oak: 5 };
  }
  if (matchKeywords(source, ['sangiovese', 'brunello', 'chianti'])) {
    return { tannin: 8, acidity: 7, body: 8, sweetness: 1, oak: 6 };
  }
  if (matchKeywords(source, ['chardonnay', 'chablis'])) {
    return { tannin: 1, acidity: 9, body: 6, sweetness: 1, oak: 3 };
  }
  if (matchKeywords(source, ['cabernet', 'bordeaux'])) {
    return { tannin: 8, acidity: 6, body: 9, sweetness: 1, oak: 7 };
  }
  if (matchKeywords(source, ['pinot noir'])) {
    return { tannin: 4, acidity: 7, body: 5, sweetness: 2, oak: 4 };
  }
  return { tannin: 6, acidity: 6, body: 6, sweetness: 2, oak: 5 };
}

function deriveWheel(varietal?: string | null): Record<string, number> {
  const v = (varietal ?? '').toLowerCase();
  if (v.includes('nebbiolo')) {
    return { 'Rose Petal': 8, 'Tar': 7, 'Sour Cherry': 7, 'Truffle': 5, 'Star Anise': 4, 'Raspberry': 5, 'Dried Herb': 6, 'Iron': 4 };
  }
  if (v.includes('sangiovese')) {
    return { 'Dried Cherry': 9, 'Leather': 6, 'Tobacco': 5, 'Earth': 8, 'Violet': 4, 'Plum': 6, 'Anise': 3, 'Forest Floor': 7 };
  }
  if (v.includes('chardonnay')) {
    return { 'Lemon Zest': 8, 'Oyster Shell': 9, 'Green Apple': 7, 'Flint': 8, 'White Flower': 5, 'Beeswax': 4, 'Almond': 4, 'Chalk': 8 };
  }
  if (v.includes('cabernet')) {
    return { 'Blackcurrant': 9, 'Cedar': 7, 'Dark Plum': 7, 'Graphite': 6, 'Tobacco': 5, 'Vanilla': 4, 'Mint': 3, 'Earth': 5 };
  }
  if (v.includes('pinot')) {
    return { 'Red Cherry': 9, 'Raspberry': 7, 'Rose': 6, 'Earth': 6, 'Mushroom': 5, 'Vanilla': 4, 'Clove': 3, 'Smoke': 4 };
  }
  return { 'Red Fruit': 7, 'Earth': 6, 'Spice': 5, 'Oak': 5, 'Floral': 4, 'Mineral': 5, 'Dark Fruit': 6, 'Herb': 4 };
}

function deriveCoords(region?: string | null, country?: string | null): WineCoords {
  const source = `${region ?? ''} ${country ?? ''}`.toLowerCase();
  if (source.includes('tuscany') || source.includes('toscana')) return { lat: 43.3, lon: 11.3 };
  if (source.includes('montalcino')) return { lat: 43.05, lon: 11.49 };
  if (source.includes('barolo') || source.includes('piedmont') || source.includes('piemonte')) return { lat: 44.61, lon: 7.94 };
  if (source.includes('chablis')) return { lat: 47.81, lon: 3.80 };
  if (source.includes('burgundy') || source.includes('bourgogne')) return { lat: 47.0, lon: 4.9 };
  if (source.includes('bordeaux')) return { lat: 44.84, lon: -0.57 };
  if (source.includes('rhone') || source.includes('rhône')) return { lat: 44.4, lon: 4.9 };
  if (source.includes('champagne')) return { lat: 49.05, lon: 4.03 };
  if (source.includes('france')) return { lat: 46.6, lon: 2.3 };
  if (source.includes('italy') || source.includes('italia')) return { lat: 42.5, lon: 12.5 };
  if (source.includes('spain') || source.includes('rioja')) return { lat: 40.4, lon: -3.7 };
  if (source.includes('germany') || source.includes('mosel')) return { lat: 51.2, lon: 9.9 };
  return { lat: 45.0, lon: 8.0 };
}

function deriveCountry(region?: string | null): string {
  const r = (region ?? '').toLowerCase();
  if (['tuscany', 'piedmont', 'veneto', 'toscana', 'piemonte', 'sicily', 'barolo', 'montalcino', 'chianti'].some((x) => r.includes(x))) return 'Italy';
  if (['burgundy', 'bordeaux', 'chablis', 'rhone', 'rhône', 'champagne', 'alsace', 'loire', 'bourgogne'].some((x) => r.includes(x))) return 'France';
  if (['rioja', 'ribera', 'priorat'].some((x) => r.includes(x))) return 'Spain';
  if (['mosel', 'rheingau', 'pfalz'].some((x) => r.includes(x))) return 'Germany';
  if (['napa', 'sonoma', 'willamette'].some((x) => r.includes(x))) return 'USA';
  return 'Italy';
}

function deriveGrape(wineName: string, varietal?: string | null): string {
  if (varietal) return varietal;
  const n = wineName.toLowerCase();
  if (n.includes('brunello')) return 'Sangiovese (Brunello clone)';
  if (n.includes('barolo') || n.includes('barbaresco')) return 'Nebbiolo';
  if (n.includes('chianti')) return 'Sangiovese';
  if (n.includes('chablis') || n.includes('chardonnay')) return 'Chardonnay';
  if (n.includes('pinot noir')) return 'Pinot Noir';
  if (n.includes('cabernet')) return 'Cabernet Sauvignon';
  return 'Red blend';
}

function deriveDrinkWindow(vintage?: number | null): DrinkWindow {
  const base = vintage ?? 2018;
  const ageability = 8;
  return { from: base + 3, peak: base + ageability, until: base + ageability * 2 };
}

function derivePairs(wineName: string, region?: string | null): string[] {
  const source = `${wineName} ${region ?? ''}`.toLowerCase();
  if (source.includes('brunello') || source.includes('sangiovese')) {
    return ['Bistecca alla Fiorentina', 'Aged pecorino', 'Wild boar ragù'];
  }
  if (source.includes('barolo') || source.includes('nebbiolo')) {
    return ['Brasato al Barolo', 'White truffle risotto', 'Aged comté'];
  }
  if (source.includes('chablis') || source.includes('chardonnay')) {
    return ['Plateau de fruits de mer', 'Beurre blanc turbot', 'Comté affiné'];
  }
  return ['Roasted meat', 'Aged cheese', 'Mushroom dishes'];
}

// Enrich a raw WineRecommendation with derived visual fields.
// Phase 5 will replace these with real backend-provided values.
export function enrichWine(wine: WineRecommendation): EnrichedWine {
  const color = derivePalette(undefined, wine.region);
  const country = deriveCountry(wine.region);
  const coords = deriveCoords(wine.region, country);
  const grape = deriveGrape(wine.wineName, undefined);
  const bars = deriveBars(undefined, wine.region);
  const wheel = deriveWheel(undefined);

  return {
    ...wine,
    id: `wine-${wine.rank}`,
    name: wine.wineName,
    country,
    appellation: wine.region ?? 'Unknown Appellation',
    coords,
    grape,
    abv: 13.5,
    drink: deriveDrinkWindow(wine.vintage),
    color,
    bars,
    wheel,
    nose: extractNose(wine.reasoning),
    palate: wine.reasoning,
    fits: wine.fitMarkers ?? [],
    pairs: derivePairs(wine.wineName, wine.region),
    critic: { score: 0, source: 'Editor' },
  };
}

function extractNose(reasoning: string): string {
  const sentence = reasoning.split('.')[0] ?? reasoning;
  const words = sentence.split(/[\s,]+/).slice(0, 6);
  return words.join(' · ').toLowerCase();
}
