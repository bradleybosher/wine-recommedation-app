import type { CSSProperties } from 'react';
import { INK, INK_SOFT, PALETTES, typeScale, type WinePalette } from '@/design/tokens';

interface Props {
  palette: WinePalette;
  grape?: string | null;
  align?: 'left' | 'center' | 'right';
  style?: CSSProperties;
}

// Map a palette object back to a hue-agnostic wine category. Lets us render a
// textual cue ("WHITE · CHARDONNAY") alongside the GlassPour so wine type is
// readable independent of colour perception (red/green colour-blind safe).
function paletteCategory(palette: WinePalette): string {
  if (palette.glass === PALETTES.chablis.glass) return 'White';
  if (palette.glass === PALETTES.rose.glass) return 'Rosé';
  if (palette.glass === PALETTES.amber.glass) return 'Orange';
  return 'Red';
}

export default function WineTypeLabel({ palette, grape, align = 'center', style }: Props) {
  const category = paletteCategory(palette);
  const grapeText = grape?.trim();
  const text = grapeText ? `${category} · ${grapeText}` : category;

  return (
    <div
      style={{
        fontFamily: "'Cormorant Garamond', serif",
        fontSize: typeScale.micro,
        letterSpacing: 2,
        textTransform: 'uppercase',
        color: INK,
        textAlign: align,
        ...style,
      }}
    >
      <span style={{ color: INK_SOFT }}>{text}</span>
    </div>
  );
}
