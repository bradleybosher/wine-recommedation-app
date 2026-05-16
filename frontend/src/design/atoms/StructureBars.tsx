import type { WinePalette } from '@/design/tokens';
import { DEFAULT_PALETTE, typeScale } from '@/design/tokens';

interface Props {
  bars: Record<string, number>;
  palette?: WinePalette;
  labels?: string[];
  compact?: boolean;
}

export default function StructureBars({ bars, palette = DEFAULT_PALETTE, labels, compact = false }: Props) {
  const ink = palette.ink;
  const accent = palette.accent;
  const paper = palette.tint;
  const keys = labels || Object.keys(bars);

  return (
    <div style={{ display: 'grid', gap: compact ? 4 : 10, fontFamily: "'Cormorant Garamond', serif" }}>
      {keys.map((k) => {
        const v = bars[k] ?? 0;
        return (
          <div key={k} style={{ display: 'grid', gridTemplateColumns: 'minmax(70px, max-content) 1fr 22px', alignItems: 'center', gap: 10 }}>
            <span style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: typeScale.label, color: ink, opacity: 0.85, textTransform: 'lowercase' }}>
              {k}
            </span>
            <svg viewBox="0 0 200 12" preserveAspectRatio="none" width="100%" height={compact ? 10 : 14}>
              <line x1={0} y1={6} x2={200} y2={6} stroke={ink} strokeOpacity={0.25} strokeWidth={0.6} />
              {Array.from({ length: 11 }).map((_, i) => (
                <line key={i} x1={i * 20} y1={2} x2={i * 20} y2={10} stroke={ink} strokeOpacity={i % 5 === 0 ? 0.4 : 0.2} strokeWidth={0.6} />
              ))}
              <rect x={0} y={4} width={v * 20} height={4} fill={accent} opacity={0.85} />
              <circle cx={v * 20} cy={6} r={3} fill={accent} stroke={paper} strokeWidth={1} />
            </svg>
            <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: typeScale.label, color: ink, opacity: 0.7, textAlign: 'right' }}>
              {v}
            </span>
          </div>
        );
      })}
    </div>
  );
}
