import type { WinePalette } from '@/design/tokens';
import { DEFAULT_PALETTE, typeScale } from '@/design/tokens';

interface DrinkWindow {
  from: number;
  peak: number;
  until: number;
}

interface Props {
  drink: DrinkWindow;
  palette?: WinePalette;
  currentYear?: number;
}

export default function DrinkingWindow({ drink, palette = DEFAULT_PALETTE, currentYear = 2026 }: Props) {
  const ink = palette.ink;
  const accent = palette.accent;
  const start = drink.from - 2;
  const end = drink.until + 2;
  const span = end - start;
  const pct = (y: number) => ((y - start) / span) * 100;

  const years: number[] = [];
  for (let y = Math.ceil(start / 5) * 5; y <= end; y += 5) years.push(y);

  return (
    <div style={{ width: '100%', fontFamily: "'EB Garamond', serif" }}>
      <div style={{ position: 'relative', height: 24, marginBottom: 6 }}>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 11, height: 2, background: ink, opacity: 0.2 }} />
        <div style={{ position: 'absolute', left: `${pct(drink.from)}%`, right: `${100 - pct(drink.until)}%`, top: 8, height: 8, background: accent, opacity: 0.25 }} />
        <div style={{ position: 'absolute', left: `${pct(drink.from)}%`, right: `${100 - pct(drink.until)}%`, top: 11, height: 2, background: accent }} />
        <div style={{ position: 'absolute', left: `${pct(drink.peak)}%`, top: 4, width: 1, height: 16, background: accent }} />
        <div style={{ position: 'absolute', left: `${pct(drink.peak)}%`, top: -4, transform: 'translateX(-50%)', fontStyle: 'italic', fontSize: typeScale.micro, color: accent }}>
          peak
        </div>
        <div style={{ position: 'absolute', left: `${pct(currentYear)}%`, top: 4, width: 0, height: 0, borderLeft: '5px solid transparent', borderRight: '5px solid transparent', borderTop: `7px solid ${ink}`, transform: 'translateX(-50%)' }} />
      </div>
      <div style={{ position: 'relative', height: 14, fontSize: typeScale.micro, color: ink, opacity: 0.7 }}>
        {years.map((y) => (
          <span key={y} style={{ position: 'absolute', left: `${pct(y)}%`, transform: 'translateX(-50%)' }}>
            {y}
          </span>
        ))}
      </div>
    </div>
  );
}
