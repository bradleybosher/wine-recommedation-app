// Vinothèque design tokens — source of truth for all editorial colour values.

export const PAPER = '#f3e8d4';
export const PAPER_DEEP = '#ecdfc4';
export const INK = '#1f120a';
export const INK_SOFT = '#3a261b';
export const RULE = 'rgba(31,18,10,0.5)';
export const OXBLOOD = '#5e1418';

// Fluid type scale — every step grows ~15–25% from 360px to 1920px viewports.
export const typeScale = {
  micro: 'clamp(11px, 0.55vw + 9px, 13px)',
  label: 'clamp(12px, 0.6vw + 10px, 14px)',
  body: 'clamp(14px, 0.65vw + 12px, 17px)',
  bodyLg: 'clamp(15px, 0.75vw + 13px, 19px)',
  h3: 'clamp(18px, 1.0vw + 15px, 24px)',
  h2: 'clamp(22px, 1.6vw + 17px, 32px)',
  h1: 'clamp(28px, 2.4vw + 20px, 44px)',
  display: 'clamp(36px, 4.5vw + 18px, 72px)',
} as const;

export const lineHeight = {
  tight: 1.15,
  snug: 1.3,
  body: 1.55,
} as const;

// Fluid spacing scale — replaces hardcoded 22/28/40/44px paddings.
export const space = {
  xs: 'clamp(6px, 0.4vw + 4px, 10px)',
  sm: 'clamp(10px, 0.6vw + 6px, 14px)',
  md: 'clamp(16px, 1.0vw + 10px, 22px)',
  lg: 'clamp(22px, 1.6vw + 14px, 36px)',
  xl: 'clamp(32px, 2.6vw + 18px, 56px)',
} as const;

// Editorial measure — prevents text sprawl on ultrawide displays.
export const PAGE_MAX_WIDTH = 1280;

export interface WinePalette {
  glass: string;
  tint: string;
  ink: string;
  accent: string;
  outline?: string;
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
    glass: '#b8932a',
    tint: '#f0e0a8',
    ink: '#3d2e08',
    accent: '#8a6e12',
    outline: INK,
  } satisfies WinePalette,
  rose: {
    glass: '#c44a6a',
    tint: '#f7d8e0',
    ink: '#3d0a18',
    accent: '#962e52',
    outline: INK,
  } satisfies WinePalette,
  amber: {
    glass: '#a86420',
    tint: '#eccfa0',
    ink: '#3a1f05',
    accent: '#7a4810',
  } satisfies WinePalette,
} as const;

export type PaletteName = keyof typeof PALETTES;

export const DEFAULT_PALETTE: WinePalette = {
  glass: '#7d1f24',
  tint: '#f4dcd3',
  ink: '#3a0d10',
  accent: '#9a2a30',
};
