import type { WinePalette } from '@/design/tokens';
import { DEFAULT_PALETTE } from '@/design/tokens';

const COUNTRY_PATHS: Record<string, string> = {
  Italy: 'M48 10 q-4 12 -2 22 q3 14 -2 24 q-3 8 4 18 q3 6 8 8 q4 2 6 8 q3 6 8 6 q5 0 6 -4 q1 -3 6 -3 q5 0 6 -4 q1 -4 -3 -8 q-4 -3 -6 -9 q-2 -6 -6 -8 q-4 -2 -6 -8 q-2 -7 -6 -10 q-4 -3 -6 -10 q-2 -7 -7 -12 z M30 78 q-4 4 0 8 q4 4 8 0 q3 -2 0 -6 q-3 -4 -8 -2 z',
  France: 'M14 22 q-4 8 0 16 q4 8 0 18 q-2 8 6 14 q8 6 16 4 q8 -2 14 4 q6 6 14 0 q8 -8 4 -18 q-4 -10 4 -16 q8 -6 0 -14 q-6 -6 -16 -2 q-10 4 -18 -2 q-8 -6 -16 -2 q-8 4 -8 -2 z',
};

const COUNTRY_BOX: Record<string, { w: number; h: number; latRange: [number, number]; lonRange: [number, number] }> = {
  Italy:  { w: 100, h: 110, latRange: [36, 47], lonRange: [7, 19] },
  France: { w: 90,  h: 90,  latRange: [42, 51], lonRange: [-5, 9] },
};

interface Props {
  country: string;
  lat?: number;
  lon?: number;
  label?: string;
  palette?: WinePalette;
  size?: number;
}

export default function RegionMap({ country, lat, lon, label, palette = DEFAULT_PALETTE, size = 120 }: Props) {
  const path = COUNTRY_PATHS[country] ?? COUNTRY_PATHS.Italy;
  const box = COUNTRY_BOX[country] ?? COUNTRY_BOX.Italy;
  const ink = palette.ink;
  const accent = palette.accent;

  const xN = lon != null ? (lon - box.lonRange[0]) / (box.lonRange[1] - box.lonRange[0]) : 0.5;
  const yN = lat != null ? 1 - (lat - box.latRange[0]) / (box.latRange[1] - box.latRange[0]) : 0.5;
  const cx = 20 + xN * 60;
  const cy = 14 + yN * 70;

  return (
    <svg viewBox="0 0 100 100" width={size} height={size}>
      <path d={path} fill="none" stroke={ink} strokeOpacity={0.55} strokeWidth={0.8} strokeLinejoin="round" />
      <circle cx={cx} cy={cy} r={6} fill="none" stroke={accent} strokeOpacity={0.4} strokeWidth={0.6} />
      <circle cx={cx} cy={cy} r={2.5} fill={accent} />
      <line x1={cx} y1={cy} x2={92} y2={cy} stroke={ink} strokeOpacity={0.35} strokeDasharray="1 2" strokeWidth={0.5} />
      {label && (
        <text x={94} y={cy + 2} fontSize={6} fontFamily="'EB Garamond', serif" fontStyle="italic" textAnchor="end" fill={ink}>
          {label}
        </text>
      )}
    </svg>
  );
}
