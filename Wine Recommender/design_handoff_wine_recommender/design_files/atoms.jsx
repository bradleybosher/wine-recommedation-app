// Shared visual atoms used by both variations:
//   FlavorWheel  — radar/spider chart of aroma spokes
//   StructureBars — printed-scale tannin/acid/body bars
//   RegionMap     — minimal Italy/France silhouette with locator dot
//   GlassPour     — angled wine in a glass, tinted to the wine's actual color
//   Ornament      — printer's ornament / fleuron-style SVG rules
//   ColorSwatch   — rim-to-core swatch
//
// All atoms accept a `palette` prop ({ ink, paper, accent, glass, tint }) so
// they can be tinted per-wine, per-variation.

const { useMemo } = React;

// ──────────────────────────────────────────────────────────
// Flavor / aroma wheel — radar polygon over labelled spokes.
function FlavorWheel({ data, size = 220, palette, label = true, rings = 4 }) {
  const entries = Object.entries(data);
  const n = entries.length;
  const cx = size / 2, cy = size / 2;
  const maxR = size * 0.34;
  const ink = palette?.ink || '#2a1a10';
  const accent = palette?.accent || '#8a2a2e';
  const tint = palette?.tint || '#f4dcd3';

  const angle = (i) => (i / n) * Math.PI * 2 - Math.PI / 2;
  const pt = (i, r) => [cx + Math.cos(angle(i)) * r, cy + Math.sin(angle(i)) * r];

  const poly = entries.map(([, v], i) => {
    const r = (v / 10) * maxR;
    const [x, y] = pt(i, r);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} style={{ overflow: 'visible' }}>
      {/* concentric rings */}
      {Array.from({ length: rings }).map((_, i) => {
        const r = ((i + 1) / rings) * maxR;
        return <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={ink} strokeOpacity={0.12} strokeWidth={0.6} />;
      })}
      {/* spokes */}
      {entries.map((_, i) => {
        const [x, y] = pt(i, maxR);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke={ink} strokeOpacity={0.18} strokeWidth={0.6} />;
      })}
      {/* polygon */}
      <polygon points={poly} fill={accent} fillOpacity={0.18} stroke={accent} strokeWidth={1.2} />
      {/* spoke dots */}
      {entries.map(([, v], i) => {
        const r = (v / 10) * maxR;
        const [x, y] = pt(i, r);
        return <circle key={i} cx={x} cy={y} r={2} fill={accent} />;
      })}
      {/* labels */}
      {label && entries.map(([k], i) => {
        const [x, y] = pt(i, maxR + 14);
        const a = angle(i);
        const anchor = Math.abs(Math.cos(a)) < 0.3 ? 'middle' : (Math.cos(a) > 0 ? 'start' : 'end');
        return (
          <text key={k} x={x} y={y} fontSize={9} fontFamily="'Cormorant Garamond', serif" fill={ink}
            textAnchor={anchor} dominantBaseline="middle" letterSpacing="0.5">
            {k.toUpperCase()}
          </text>
        );
      })}
    </svg>
  );
}

// ──────────────────────────────────────────────────────────
// Structure bars: an old-print scale with ticks and a filled segment.
function StructureBars({ bars, palette, labels, compact = false }) {
  const ink = palette?.ink || '#2a1a10';
  const accent = palette?.accent || '#8a2a2e';
  const tint = palette?.tint || '#f4dcd3';
  const keys = labels || Object.keys(bars);
  return (
    <div style={{ display: 'grid', gap: compact ? 4 : 10, fontFamily: "'Cormorant Garamond', serif" }}>
      {keys.map((k) => {
        const v = bars[k] || 0;
        return (
          <div key={k} style={{ display: 'grid', gridTemplateColumns: '74px 1fr 18px', alignItems: 'center', gap: 10 }}>
            <span style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: 13, color: ink, opacity: 0.78, textTransform: 'lowercase' }}>{k}</span>
            <svg viewBox="0 0 200 12" preserveAspectRatio="none" width="100%" height={compact ? 10 : 14}>
              <line x1={0} y1={6} x2={200} y2={6} stroke={ink} strokeOpacity={0.25} strokeWidth={0.6} />
              {Array.from({ length: 11 }).map((_, i) => (
                <line key={i} x1={i * 20} y1={2} x2={i * 20} y2={10} stroke={ink} strokeOpacity={i % 5 === 0 ? 0.4 : 0.2} strokeWidth={0.6} />
              ))}
              <rect x={0} y={4} width={v * 20} height={4} fill={accent} opacity={0.85} />
              <circle cx={v * 20} cy={6} r={3} fill={accent} stroke={palette?.paper || '#f5ecdc'} strokeWidth={1} />
            </svg>
            <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 12, color: ink, opacity: 0.6, textAlign: 'right' }}>{v}</span>
          </div>
        );
      })}
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Tiny region map — Italy / France stylised silhouette + locator dot.
// Coords use a crude lat/lon → svg projection per country.
const COUNTRY_PATHS = {
  // simplified silhouettes; kept small + clean
  Italy: 'M48 10 q-4 12 -2 22 q3 14 -2 24 q-3 8 4 18 q3 6 8 8 q4 2 6 8 q3 6 8 6 q5 0 6 -4 q1 -3 6 -3 q5 0 6 -4 q1 -4 -3 -8 q-4 -3 -6 -9 q-2 -6 -6 -8 q-4 -2 -6 -8 q-2 -7 -6 -10 q-4 -3 -6 -10 q-2 -7 -7 -12 z M30 78 q-4 4 0 8 q4 4 8 0 q3 -2 0 -6 q-3 -4 -8 -2 z',
  France: 'M14 22 q-4 8 0 16 q4 8 0 18 q-2 8 6 14 q8 6 16 4 q8 -2 14 4 q6 6 14 0 q8 -8 4 -18 q-4 -10 4 -16 q8 -6 0 -14 q-6 -6 -16 -2 q-10 4 -18 -2 q-8 -6 -16 -2 q-8 4 -8 -2 z',
};
const COUNTRY_BOX = { Italy: { w: 100, h: 110, latRange: [36, 47], lonRange: [7, 19] }, France: { w: 90, h: 90, latRange: [42, 51], lonRange: [-5, 9] } };

function RegionMap({ country, lat, lon, label, palette, size = 120 }) {
  const path = COUNTRY_PATHS[country] || COUNTRY_PATHS.Italy;
  const box = COUNTRY_BOX[country] || COUNTRY_BOX.Italy;
  const ink = palette?.ink || '#2a1a10';
  const accent = palette?.accent || '#8a2a2e';
  // normalize lat/lon into the silhouette's drawn bounding box (rough)
  const xN = lon != null ? ((lon - box.lonRange[0]) / (box.lonRange[1] - box.lonRange[0])) : 0.5;
  const yN = lat != null ? (1 - (lat - box.latRange[0]) / (box.latRange[1] - box.latRange[0])) : 0.5;
  // map drawn shape footprint (approx)
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

// ──────────────────────────────────────────────────────────
// Wine in a glass — tinted to wine's actual color
function GlassPour({ palette, size = 100, fill = 0.55 }) {
  const c = palette?.glass || '#7d1f24';
  const ink = palette?.ink || '#2a1a10';
  // glass bowl: roughly ellipse with stem
  const w = size, h = size * 1.4;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width={w} height={h} style={{ overflow: 'visible' }}>
      <defs>
        <clipPath id={`bowl-${c.replace('#', '')}`}>
          <path d={`M ${w * 0.15} ${h * 0.05} q ${w * 0.05} ${h * 0.45} ${w * 0.35} ${h * 0.5} q ${w * 0.3} -0.05 ${w * 0.35} -${h * 0.5} z`} />
        </clipPath>
      </defs>
      {/* wine fill */}
      <rect x={0} y={h * (0.55 - fill * 0.5)} width={w} height={h} fill={c} clipPath={`url(#bowl-${c.replace('#', '')})`} opacity={0.85} />
      {/* glass outline */}
      <path d={`M ${w * 0.15} ${h * 0.05} q ${w * 0.05} ${h * 0.45} ${w * 0.35} ${h * 0.5} q ${w * 0.3} -0.05 ${w * 0.35} -${h * 0.5}`} fill="none" stroke={ink} strokeOpacity={0.6} strokeWidth={0.8} />
      <line x1={w * 0.5} y1={h * 0.55} x2={w * 0.5} y2={h * 0.92} stroke={ink} strokeOpacity={0.6} strokeWidth={0.8} />
      <line x1={w * 0.3} y1={h * 0.95} x2={w * 0.7} y2={h * 0.95} stroke={ink} strokeOpacity={0.6} strokeWidth={1.2} />
    </svg>
  );
}

// ──────────────────────────────────────────────────────────
// Bottle silhouette — Bordeaux/Burgundy variants
function Bottle({ palette, shape = 'bordeaux', size = 60 }) {
  const c = palette?.glass || '#7d1f24';
  const ink = palette?.ink || '#2a1a10';
  const tint = palette?.tint || '#f4dcd3';
  const w = size, h = size * 3;
  const isBurg = shape === 'burgundy';
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width={w} height={h}>
      {/* bottle body */}
      <path d={
        isBurg
          ? `M ${w*0.35} 0 L ${w*0.65} 0 L ${w*0.65} ${h*0.18} Q ${w*0.65} ${h*0.28} ${w*0.85} ${h*0.42} Q ${w} ${h*0.55} ${w} ${h*0.95} L ${w} ${h} L 0 ${h} L 0 ${h*0.95} Q 0 ${h*0.55} ${w*0.15} ${h*0.42} Q ${w*0.35} ${h*0.28} ${w*0.35} ${h*0.18} Z`
          : `M ${w*0.35} 0 L ${w*0.65} 0 L ${w*0.65} ${h*0.22} Q ${w*0.65} ${h*0.32} ${w*0.9} ${h*0.42} L ${w*0.9} ${h*0.95} Q ${w*0.9} ${h} ${w*0.78} ${h} L ${w*0.22} ${h} Q ${w*0.1} ${h} ${w*0.1} ${h*0.95} L ${w*0.1} ${h*0.42} Q ${w*0.35} ${h*0.32} ${w*0.35} ${h*0.22} Z`
      } fill={c} opacity={0.92} stroke={ink} strokeOpacity={0.5} strokeWidth={0.6} />
      {/* label */}
      <rect x={w*0.08} y={h*0.55} width={w*0.84} height={h*0.28} fill={tint} stroke={ink} strokeOpacity={0.3} strokeWidth={0.4} />
      <line x1={w*0.18} y1={h*0.62} x2={w*0.82} y2={h*0.62} stroke={ink} strokeOpacity={0.5} strokeWidth={0.5} />
      <line x1={w*0.18} y1={h*0.72} x2={w*0.82} y2={h*0.72} stroke={ink} strokeOpacity={0.25} strokeWidth={0.4} />
      <line x1={w*0.25} y1={h*0.76} x2={w*0.75} y2={h*0.76} stroke={ink} strokeOpacity={0.25} strokeWidth={0.4} />
    </svg>
  );
}

// ──────────────────────────────────────────────────────────
// Ornaments — fleurons / printer's ornaments / rules
function Fleuron({ size = 26, color = '#2a1a10' }) {
  return (
    <svg viewBox="0 0 40 20" width={size * 2} height={size} style={{ display: 'inline-block' }}>
      <path d="M0 10 L 14 10 M 26 10 L 40 10" stroke={color} strokeWidth={0.7} />
      <path d="M 20 4 Q 16 10 20 16 Q 24 10 20 4 Z" fill={color} opacity={0.9} />
      <circle cx={20} cy={10} r={1.2} fill={color} />
      <circle cx={14.5} cy={10} r={0.9} fill={color} />
      <circle cx={25.5} cy={10} r={0.9} fill={color} />
    </svg>
  );
}

function RuleDouble({ color = '#2a1a10', opacity = 0.5 }) {
  return (
    <div style={{ borderTop: `1px solid ${color}`, opacity, padding: '2px 0' }}>
      <div style={{ borderTop: `0.5px solid ${color}`, marginTop: 2 }} />
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Drinking window — annotated timeline
function DrinkingWindow({ drink, palette, currentYear = 2026 }) {
  const ink = palette?.ink || '#2a1a10';
  const accent = palette?.accent || '#8a2a2e';
  const start = drink.from - 2, end = drink.until + 2;
  const span = end - start;
  const pct = (y) => ((y - start) / span) * 100;
  const years = [];
  for (let y = Math.ceil(start / 5) * 5; y <= end; y += 5) years.push(y);
  return (
    <div style={{ width: '100%', fontFamily: "'EB Garamond', serif" }}>
      <div style={{ position: 'relative', height: 24, marginBottom: 6 }}>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 11, height: 2, background: ink, opacity: 0.2 }} />
        <div style={{ position: 'absolute', left: `${pct(drink.from)}%`, right: `${100 - pct(drink.until)}%`, top: 8, height: 8, background: accent, opacity: 0.25 }} />
        <div style={{ position: 'absolute', left: `${pct(drink.from)}%`, right: `${100 - pct(drink.until)}%`, top: 11, height: 2, background: accent }} />
        {/* peak */}
        <div style={{ position: 'absolute', left: `${pct(drink.peak)}%`, top: 4, width: 1, height: 16, background: accent }} />
        <div style={{ position: 'absolute', left: `${pct(drink.peak)}%`, top: -4, transform: 'translateX(-50%)', fontStyle: 'italic', fontSize: 10, color: accent }}>peak</div>
        {/* current */}
        <div style={{ position: 'absolute', left: `${pct(currentYear)}%`, top: 4, width: 0, height: 0, borderLeft: '5px solid transparent', borderRight: '5px solid transparent', borderTop: `7px solid ${ink}`, transform: 'translateX(-50%)' }} />
      </div>
      <div style={{ position: 'relative', height: 14, fontSize: 10, color: ink, opacity: 0.6 }}>
        {years.map(y => (
          <span key={y} style={{ position: 'absolute', left: `${pct(y)}%`, transform: 'translateX(-50%)' }}>{y}</span>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, {
  FlavorWheel, StructureBars, RegionMap, GlassPour, Bottle, Fleuron, RuleDouble, DrinkingWindow,
});
