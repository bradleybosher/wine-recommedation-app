import type { WinePalette } from '@/design/tokens';
import { DEFAULT_PALETTE } from '@/design/tokens';

interface Props {
  palette?: WinePalette;
  shape?: 'bordeaux' | 'burgundy';
  size?: number;
}

export default function Bottle({ palette = DEFAULT_PALETTE, shape = 'bordeaux', size = 60 }: Props) {
  const c = palette.glass;
  const ink = palette.ink;
  const tint = palette.tint;
  const w = size;
  const h = size * 3;
  const isBurg = shape === 'burgundy';

  const bodyPath = isBurg
    ? `M ${w*0.35} 0 L ${w*0.65} 0 L ${w*0.65} ${h*0.18} Q ${w*0.65} ${h*0.28} ${w*0.85} ${h*0.42} Q ${w} ${h*0.55} ${w} ${h*0.95} L ${w} ${h} L 0 ${h} L 0 ${h*0.95} Q 0 ${h*0.55} ${w*0.15} ${h*0.42} Q ${w*0.35} ${h*0.28} ${w*0.35} ${h*0.18} Z`
    : `M ${w*0.35} 0 L ${w*0.65} 0 L ${w*0.65} ${h*0.22} Q ${w*0.65} ${h*0.32} ${w*0.9} ${h*0.42} L ${w*0.9} ${h*0.95} Q ${w*0.9} ${h} ${w*0.78} ${h} L ${w*0.22} ${h} Q ${w*0.1} ${h} ${w*0.1} ${h*0.95} L ${w*0.1} ${h*0.42} Q ${w*0.35} ${h*0.32} ${w*0.35} ${h*0.22} Z`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} width={w} height={h}>
      <path d={bodyPath} fill={c} opacity={0.92} stroke={ink} strokeOpacity={0.5} strokeWidth={0.6} />
      <rect x={w*0.08} y={h*0.55} width={w*0.84} height={h*0.28} fill={tint} stroke={ink} strokeOpacity={0.3} strokeWidth={0.4} />
      <line x1={w*0.18} y1={h*0.62} x2={w*0.82} y2={h*0.62} stroke={ink} strokeOpacity={0.5} strokeWidth={0.5} />
      <line x1={w*0.18} y1={h*0.72} x2={w*0.82} y2={h*0.72} stroke={ink} strokeOpacity={0.25} strokeWidth={0.4} />
      <line x1={w*0.25} y1={h*0.76} x2={w*0.75} y2={h*0.76} stroke={ink} strokeOpacity={0.25} strokeWidth={0.4} />
    </svg>
  );
}
