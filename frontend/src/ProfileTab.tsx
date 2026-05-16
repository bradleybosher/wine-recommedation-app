import React, { useEffect, useState } from 'react';
import { profileSummaryProfileSummaryGet } from '@/client';
import type { ProfileSummaryResponse, TasteMarkers } from '@/client/types.gen';
import { INK, INK_SOFT, OXBLOOD, RULE, typeScale, lineHeight } from '@/design/tokens';
import { Loader2 } from 'lucide-react';

// ─── Helpers ────────────────────────────────────────────────────────────────

const MARKER_LABELS: Record<number, string> = {
  1: 'Very Low',
  2: 'Low',
  3: 'Medium',
  4: 'High',
  5: 'Very High',
};

function markerLabel(val: number): string {
  return MARKER_LABELS[Math.round(val)] ?? 'Medium';
}

function markerPercent(val: number): number {
  return Math.round((val / 5) * 100);
}

// ─── Sub-components ──────────────────────────────────────────────────────────

interface MarkerBarProps {
  label: string;
  value: number;
}

const MarkerBar: React.FC<MarkerBarProps> = ({ label, value }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
    <span
      style={{
        width: 72,
        fontFamily: "'Cormorant Garamond', serif",
        fontSize: typeScale.micro,
        letterSpacing: 1,
        textTransform: 'uppercase',
        color: INK_SOFT,
        flexShrink: 0,
      }}
    >
      {label}
    </span>
    <div
      style={{
        flex: 1,
        height: 2,
        background: RULE,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          height: '100%',
          width: `${markerPercent(value)}%`,
          background: INK,
          transition: 'width 0.5s ease',
        }}
      />
    </div>
    <span
      style={{
        width: 64,
        fontFamily: "'EB Garamond', serif",
        fontStyle: 'italic',
        fontSize: typeScale.label,
        color: INK_SOFT,
        textAlign: 'right',
        flexShrink: 0,
      }}
    >
      {markerLabel(value)}
    </span>
  </div>
);

const sectionHead = (label: string): React.ReactElement => (
  <div
    style={{
      fontFamily: "'Cormorant Garamond', serif",
      fontStyle: 'italic',
      fontSize: typeScale.micro,
      letterSpacing: 3,
      textTransform: 'uppercase',
      color: OXBLOOD,
      marginBottom: 12,
    }}
  >
    {label}
  </div>
);

const tagStyle: React.CSSProperties = {
  fontFamily: "'EB Garamond', serif",
  fontSize: typeScale.label,
  padding: '2px 8px',
  border: `1px solid ${RULE}`,
  color: INK_SOFT,
};

// ─── Main Component ──────────────────────────────────────────────────────────

const ProfileTab: React.FC = () => {
  const [data, setData] = useState<ProfileSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    profileSummaryProfileSummaryGet()
      .then((res) => setData(res.data ?? null))
      .catch((err) => setError(err?.message ?? 'Failed to load profile'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '60px 0',
          gap: 12,
        }}
      >
        <Loader2
          className="animate-spin"
          style={{ width: 28, height: 28, color: INK_SOFT }}
          strokeWidth={1.5}
        />
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.body,
            color: INK_SOFT,
          }}
        >
          Building your palate profile…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          border: `1px solid ${RULE}`,
          padding: '10px 16px',
          fontFamily: "'EB Garamond', serif",
          fontSize: typeScale.body,
          color: OXBLOOD,
        }}
      >
        {error}
      </div>
    );
  }

  if (!data) return null;

  const markers = data.tasteMarkers as TasteMarkers | null | undefined;
  const stats = data.cellarStats;

  const vintageRange =
    stats?.vintageOldest && stats?.vintageNewest
      ? `${stats.vintageOldest} – ${stats.vintageNewest}`
      : '—';

  const section = (content: React.ReactNode): React.ReactElement => (
    <div
      style={{
        borderTop: `1px solid ${RULE}`,
        paddingTop: 20,
        paddingBottom: 20,
      }}
    >
      {content}
    </div>
  );

  return (
    <div>
      {/* ── Palate Portrait ─────────────────────────────────────────────── */}
      {section(
        <>
          {sectionHead('Palate Portrait')}
          {data.styleSummary ? (
            <div
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: typeScale.bodyLg,
                color: INK,
                lineHeight: lineHeight.body,
              }}
            >
              "{data.styleSummary}"
            </div>
          ) : (
            <div
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: typeScale.body,
                color: INK_SOFT,
                opacity: 0.6,
              }}
            >
              Run a recommendation to generate your personalised palate portrait.
            </div>
          )}
        </>
      )}

      {/* ── Cellar at a Glance ──────────────────────────────────────────── */}
      {stats &&
        section(
          <>
            {sectionHead('Cellar at a Glance')}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 0 }}>
              {[
                { label: 'Total Bottles', value: stats.totalBottles ?? 0 },
                { label: 'Unique Wines', value: stats.uniqueWines ?? 0 },
                { label: 'Vintage Range', value: vintageRange },
              ].map(({ label, value }, i) => (
                <div
                  key={label}
                  style={{
                    borderLeft: i > 0 ? `1px solid ${RULE}` : undefined,
                    paddingLeft: i > 0 ? 20 : 0,
                    paddingRight: 20,
                  }}
                >
                  <div
                    style={{
                      fontFamily: "'Cormorant Garamond', serif",
                      fontSize: typeScale.h1,
                      color: INK,
                      letterSpacing: -0.5,
                    }}
                  >
                    {value}
                  </div>
                  <div
                    style={{
                      fontFamily: "'Cormorant Garamond', serif",
                      fontSize: typeScale.micro,
                      letterSpacing: 2,
                      textTransform: 'uppercase',
                      color: INK_SOFT,
                      marginTop: 2,
                    }}
                  >
                    {label}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

      {/* ── Taste Profile Markers ────────────────────────────────────────── */}
      {markers &&
        section(
          <>
            {sectionHead('Taste Profile')}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <MarkerBar label="Acidity" value={markers.acidity} />
              <MarkerBar label="Tannin" value={markers.tannin} />
              <MarkerBar label="Body" value={markers.body} />
              <MarkerBar label="Oak" value={markers.oak} />
            </div>
            <div
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: typeScale.micro,
                color: INK_SOFT,
                marginTop: 12,
                opacity: 0.5,
              }}
            >
              Derived from your tasting note descriptors — indicative, not prescriptive.
            </div>
          </>
        )}

      {/* ── Flavour Preferences ─────────────────────────────────────────── */}
      {data.preferredDescriptors && data.preferredDescriptors.length > 0 &&
        section(
          <>
            {sectionHead('Flavour Preferences')}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {data.preferredDescriptors.map((d, i) => (
                <span key={i} style={tagStyle}>{d}</span>
              ))}
            </div>
          </>
        )}

      {/* ── Styles to Avoid ──────────────────────────────────────────────── */}
      {data.avoidedStyles && data.avoidedStyles.length > 0 &&
        section(
          <>
            {sectionHead('Styles to Avoid')}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {data.avoidedStyles.map((s, i) => (
                <span key={i} style={{ ...tagStyle, borderColor: OXBLOOD, color: OXBLOOD }}>{s}</span>
              ))}
            </div>
          </>
        )}

      {/* ── Top Varietals & Regions ──────────────────────────────────────── */}
      {((data.topVarietals && data.topVarietals.length > 0) || (data.topRegions && data.topRegions.length > 0)) &&
        section(
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 24 }}>
            {data.topVarietals && data.topVarietals.length > 0 && (
              <div>
                {sectionHead('Top Varietals')}
                <ol style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {data.topVarietals.map((v, i) => (
                    <li
                      key={i}
                      style={{ display: 'flex', alignItems: 'center', gap: 10 }}
                    >
                      <span
                        style={{
                          fontFamily: "'Cormorant Garamond', serif",
                          fontSize: typeScale.label,
                          color: INK_SOFT,
                          width: 16,
                          flexShrink: 0,
                        }}
                      >
                        {i + 1}
                      </span>
                      <span style={{ fontFamily: "'EB Garamond', serif", fontSize: typeScale.body, color: INK }}>{v}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {data.topRegions && data.topRegions.length > 0 && (
              <div>
                {sectionHead('Top Regions')}
                <ol style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {data.topRegions.map((r, i) => (
                    <li
                      key={i}
                      style={{ display: 'flex', alignItems: 'center', gap: 10 }}
                    >
                      <span
                        style={{
                          fontFamily: "'Cormorant Garamond', serif",
                          fontSize: typeScale.label,
                          color: INK_SOFT,
                          width: 16,
                          flexShrink: 0,
                        }}
                      >
                        {i + 1}
                      </span>
                      <span style={{ fontFamily: "'EB Garamond', serif", fontSize: typeScale.body, color: INK }}>{r}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}

      {/* ── Average Spend ────────────────────────────────────────────────── */}
      {data.avgSpend != null &&
        section(
          <>
            {sectionHead('Average Bottle Spend')}
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: typeScale.h1,
                color: INK,
                letterSpacing: -0.5,
              }}
            >
              ${data.avgSpend}
            </div>
          </>
        )}
    </div>
  );
};

export default ProfileTab;
