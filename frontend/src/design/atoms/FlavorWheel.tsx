import type { WinePalette } from '@/design/tokens';
import { DEFAULT_PALETTE, INK } from '@/design/tokens';

interface Props {
  data: Record<string, number>;
  size?: number;
  palette?: WinePalette;
  label?: boolean;
  rings?: number;
}

export default function FlavorWheel({ data, size = 220, palette = DEFAULT_PALETTE, label = true, rings = 4 }: Props) {
  const entries = Object.entries(data);
  const n = entries.length;
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size * 0.34;
  const ink = palette.ink;
  const accent = palette.accent;

  const angle = (i: number) => (i / n) * Math.PI * 2 - Math.PI / 2;
  const pt = (i: number, r: number): [number, number] => [
    cx + Math.cos(angle(i)) * r,
    cy + Math.sin(angle(i)) * r,
  ];

  const poly = entries
    .map(([, v], i) => {
      const r = (v / 10) * maxR;
      const [x, y] = pt(i, r);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} style={{ overflow: 'visible' }}>
      {Array.from({ length: rings }).map((_, i) => {
        const r = ((i + 1) / rings) * maxR;
        return <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={ink} strokeOpacity={0.12} strokeWidth={0.6} />;
      })}
      {entries.map((_, i) => {
        const [x, y] = pt(i, maxR);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke={ink} strokeOpacity={0.18} strokeWidth={0.6} />;
      })}
      <polygon points={poly} fill={accent} fillOpacity={0.18} stroke={accent} strokeWidth={1.2} />
      {entries.map(([, v], i) => {
        const r = (v / 10) * maxR;
        const [x, y] = pt(i, r);
        return <circle key={i} cx={x} cy={y} r={2} fill={accent} />;
      })}
      {label && entries.map(([k], i) => {
        const [x, y] = pt(i, maxR + 14);
        const a = angle(i);
        const anchor = Math.abs(Math.cos(a)) < 0.3 ? 'middle' : (Math.cos(a) > 0 ? 'start' : 'end');
        return (
          <text
            key={k}
            x={x}
            y={y}
            fontSize={9}
            fontFamily="'Cormorant Garamond', serif"
            fill={ink}
            textAnchor={anchor}
            dominantBaseline="middle"
            letterSpacing="0.5"
          >
            {k.toUpperCase()}
          </text>
        );
      })}
    </svg>
  );
}
