// Vinothèque design tokens — source of truth for all editorial colour values.

export const PAPER = '#f3e8d4';
export const PAPER_DEEP = '#ecdfc4';
export const INK = '#1f120a';
export const INK_SOFT = '#3a261b';
export const RULE = 'rgba(31,18,10,0.5)';
export const OXBLOOD = '#5e1418';

export interface WinePalette {
  glass: string;
  tint: string;
  ink: string;
  accent: string;
}

export const PALETTES = {
  brunello: {
    glass: '#7d1f24',
    tint: '#f4dcd3',
    ink: '#3a0d10',
    accent: '#9a2a30',
  } satisfies WinePalette,
  barolo: {
    glass: '#8a2a2e',
    tint: '#f3dad4',
    ink: '#3d1014',
    accent: '#a83339',
  } satisfies WinePalette,
  chablis: {
    glass: '#d9b743',
    tint: '#f5ecc8',
    ink: '#5a4612',
    accent: '#b89826',
  } satisfies WinePalette,
} as const;

export type PaletteName = keyof typeof PALETTES;

export const DEFAULT_PALETTE: WinePalette = {
  glass: '#7d1f24',
  tint: '#f4dcd3',
  ink: '#3a0d10',
  accent: '#9a2a30',
};
