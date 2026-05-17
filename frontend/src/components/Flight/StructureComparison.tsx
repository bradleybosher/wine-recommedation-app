import { INK_SOFT, RULE, space, typeScale } from '@/design/tokens';
import type { EnrichedWine } from '@/design/wineColor';

interface Props {
  wines: EnrichedWine[];
}

export default function StructureComparison({ wines }: Props) {
  const dimensions = ['tannin', 'acidity', 'body', 'sweetness', 'oak'] as const;

  const winesWithBars = wines.filter((w) => w.bars != null);

  if (winesWithBars.length < 2) {
    return null;
  }

  const columnCount = winesWithBars.length;
  const gridTemplateColumns = `minmax(70px, max-content) ${'1fr '.repeat(columnCount).trim()}`;

  const Bar = ({ value, wine }: { value: number; wine: EnrichedWine }) => (
    <svg viewBox="0 0 200 12" preserveAspectRatio="none" width="100%" height={10}>
      <line x1={0} y1={6} x2={200} y2={6} stroke={wine.color.ink} strokeOpacity={0.25} strokeWidth={0.6} />
      {Array.from({ length: 11 }).map((_, i) => (
        <line
          key={i}
          x1={i * 20}
          y1={2}
          x2={i * 20}
          y2={10}
          stroke={wine.color.ink}
          strokeOpacity={i % 5 === 0 ? 0.4 : 0.2}
          strokeWidth={0.6}
        />
      ))}
      <rect x={0} y={4} width={value * 20} height={4} fill={wine.color.accent} opacity={0.85} />
      <circle cx={value * 20} cy={6} r={3} fill={wine.color.accent} stroke={wine.color.tint} strokeWidth={1} />
    </svg>
  );

  return (
    <div
      style={{
        marginTop: space.lg,
        marginBottom: space.md,
        borderTop: `1px solid ${RULE}`,
        paddingTop: space.sm,
      }}
    >
      <div
        style={{
          fontFamily: "'Cormorant Garamond', serif",
          fontStyle: 'italic',
          fontSize: typeScale.micro,
          letterSpacing: 3,
          textTransform: 'uppercase',
          color: INK_SOFT,
          marginBottom: space.sm,
        }}
      >
        Structure Comparison
      </div>

      <div style={{ display: 'grid', gridTemplateColumns, gap: 6 }}>
        {/* Header row: empty + wine names */}
        <div />
        {winesWithBars.map((wine) => (
          <div
            key={`header-${wine.id}`}
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: typeScale.label,
              color: INK_SOFT,
            }}
          >
            {wine.name.split(' ')[0]}
          </div>
        ))}

        {/* Data rows */}
        {dimensions.map((dim) => (
          <div key={`row-${dim}`} style={{ display: 'contents' }}>
            <div
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: typeScale.label,
                color: INK_SOFT,
              }}
            >
              {dim}
            </div>
            {winesWithBars.map((wine) => (
              <div key={`${wine.id}-${dim}`}>
                <Bar value={wine.bars[dim]} wine={wine} />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
