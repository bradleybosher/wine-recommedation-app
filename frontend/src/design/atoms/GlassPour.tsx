import type { WinePalette } from '@/design/tokens';
import { DEFAULT_PALETTE } from '@/design/tokens';

interface Props {
  palette?: WinePalette;
  size?: number;
  fill?: number;
}

export default function GlassPour({ palette = DEFAULT_PALETTE, size = 100, fill = 0.55 }: Props) {
  const c = palette.glass;
  const ink = palette.ink;
  const w = size;
  const h = size * 1.4;
  const clipId = `bowl-${c.replace('#', '')}`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} width={w} height={h} style={{ overflow: 'visible' }}>
      <defs>
        <clipPath id={clipId}>
          <path d={`M ${w * 0.15} ${h * 0.05} q ${w * 0.05} ${h * 0.45} ${w * 0.35} ${h * 0.5} q ${w * 0.3} -0.05 ${w * 0.35} -${h * 0.5} z`} />
        </clipPath>
      </defs>
      <rect x={0} y={h * (0.55 - fill * 0.5)} width={w} height={h} fill={c} clipPath={`url(#${clipId})`} opacity={0.85} />
      {palette.outline && (
        // Hairline trace of the wine surface — gives light fills (white/rosé) a
        // recognizable silhouette against cream paper independent of hue.
        <line
          x1={w * 0.17}
          y1={h * (0.55 - fill * 0.5) + 1}
          x2={w * 0.83}
          y2={h * (0.55 - fill * 0.5) + 1}
          stroke={palette.outline}
          strokeOpacity={0.45}
          strokeWidth={0.8}
          clipPath={`url(#${clipId})`}
        />
      )}
      <path
        d={`M ${w * 0.15} ${h * 0.05} q ${w * 0.05} ${h * 0.45} ${w * 0.35} ${h * 0.5} q ${w * 0.3} -0.05 ${w * 0.35} -${h * 0.5}`}
        fill="none"
        stroke={ink}
        strokeOpacity={palette.outline ? 0.85 : 0.6}
        strokeWidth={palette.outline ? 1.1 : 0.8}
      />
      <line x1={w * 0.5} y1={h * 0.55} x2={w * 0.5} y2={h * 0.92} stroke={ink} strokeOpacity={0.6} strokeWidth={0.8} />
      <line x1={w * 0.3} y1={h * 0.95} x2={w * 0.7} y2={h * 0.95} stroke={ink} strokeOpacity={0.6} strokeWidth={1.2} />
    </svg>
  );
}
