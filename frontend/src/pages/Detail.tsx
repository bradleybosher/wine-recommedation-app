import { useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import FlavorWheel from '@/design/atoms/FlavorWheel';
import StructureBars from '@/design/atoms/StructureBars';
import RegionMap from '@/design/atoms/RegionMap';
import GlassPour from '@/design/atoms/GlassPour';
import Bottle from '@/design/atoms/Bottle';
import DrinkingWindow from '@/design/atoms/DrinkingWindow';
import Panel from '@/components/Detail/Panel';
import WineTypeLabel from '@/design/atoms/WineTypeLabel';
import { INK, INK_SOFT, OXBLOOD, PAPER, lineHeight, space, typeScale } from '@/design/tokens';
import { enrichWine } from '@/design/wineColor';
import { useRecommendations } from '@/state/recommendationStore';

const ghostBtn: React.CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: typeScale.label,
  letterSpacing: 2,
  textTransform: 'uppercase',
  padding: `${space.xs} ${space.sm}`,
  background: 'transparent',
  color: INK,
  border: `1px solid ${INK}`,
  cursor: 'pointer',
};

export default function Detail() {
  const { wineId } = useParams<{ wineId: string }>();
  const navigate = useNavigate();
  const { recommendations } = useRecommendations();

  const wine = useMemo(() => {
    if (!recommendations) return null;
    const raw = recommendations.recommendations.find(
      (_, i) => `wine-${recommendations.recommendations[i].rank}` === wineId,
    );
    return raw ? enrichWine(raw) : null;
  }, [recommendations, wineId]);

  if (!wine) {
    return (
      <PaperFrame>
        <Masthead dateline="Wine not found" />
        <div
          style={{
            padding: `${space.xl} 0`,
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.bodyLg,
            color: INK_SOFT,
            textAlign: 'center',
          }}
        >
          Wine record not found.{' '}
          <span
            onClick={() => navigate('/flight')}
            style={{ textDecoration: 'underline', cursor: 'pointer' }}
          >
            Return to the flight.
          </span>
        </div>
      </PaperFrame>
    );
  }

  const accent = wine.color.accent;
  const shape = wine.color.glass.startsWith('#d') ? 'burgundy' : 'bordeaux';

  return (
    <PaperFrame>
      <Masthead dateline={`Review № ${wine.rank.toString().padStart(2, '0')} · Editorial`} />

      {/* Band 1 — Hero */}
      <div
        style={{
          containerType: 'inline-size',
          padding: `${space.md} 0 ${space.sm}`,
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1.6fr)',
          gap: space.md,
          alignItems: 'start',
        }}
      >
        {/* Left — bottle + glass */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16 }}>
            <Bottle palette={wine.color} shape={shape} size={44} />
            <GlassPour palette={wine.color} size={80} fill={0.5} />
          </div>
          <WineTypeLabel palette={wine.color} grape={wine.grape} style={{ marginTop: 6 }} />
        </div>

        {/* Right — editorial body */}
        <div>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.micro,
              letterSpacing: 3,
              textTransform: 'uppercase',
              color: accent,
              marginBottom: 4,
            }}
          >
            {wine.region} · {wine.appellation}
          </div>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              fontSize: typeScale.display,
              lineHeight: lineHeight.tight,
              color: INK,
              letterSpacing: -1,
              marginBottom: 8,
            }}
          >
            {wine.name}
          </div>
          <div
            style={{
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.h3,
              color: INK_SOFT,
              marginBottom: 14,
            }}
          >
            {wine.producer} · {wine.vintage}
          </div>

          {/* Palate with drop cap */}
          <div
            style={{
              fontFamily: "'EB Garamond', serif",
              fontSize: typeScale.body,
              lineHeight: lineHeight.body,
              color: INK,
            }}
          >
            <span
              style={{
                float: 'left',
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: typeScale.display,
                lineHeight: 0.78,
                color: accent,
                fontStyle: 'italic',
                marginRight: 4,
                marginTop: 4,
              }}
            >
              {wine.palate[0]}
            </span>
            {wine.palate.slice(1)}
          </div>
        </div>
      </div>

      {/* RuleDouble divider */}
      <div style={{ padding: `${space.sm} 0 0` }}>
        <RuleDouble color={INK} opacity={0.45} />
      </div>

      {/* Band 2 — Triptych */}
      <div
        className="detail-panels"
        style={{
          containerType: 'inline-size',
          padding: `${space.md} 0 ${space.md}`,
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: space.md,
        }}
      >
        {/* FlavorWheel panel */}
        <Panel title="Aroma Profile" caption="Nose">
          <FlavorWheel data={wine.wheel} size={200} palette={wine.color} />
          <div
            style={{
              marginTop: 10,
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.label,
              color: INK_SOFT,
              textAlign: 'center',
              maxWidth: 180,
            }}
          >
            {wine.nose}
          </div>
        </Panel>

        {/* StructureBars panel */}
        <Panel title="Structure" caption="Palate">
          <div style={{ width: '100%', padding: `0 ${space.sm}` }}>
            <StructureBars
              bars={{
                tannin: wine.bars.tannin,
                acidity: wine.bars.acidity,
                body: wine.bars.body,
                sweetness: wine.bars.sweetness,
                oak: wine.bars.oak,
              }}
              palette={wine.color}
            />
          </div>
        </Panel>

        {/* RegionMap panel */}
        <Panel title={wine.region ?? wine.country} caption="Terroir">
          <RegionMap
            country={wine.country}
            lat={wine.coords.lat}
            lon={wine.coords.lon}
            palette={wine.color}
            size={150}
          />
          <div
            style={{
              marginTop: 8,
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.label,
              color: INK_SOFT,
              textAlign: 'center',
            }}
          >
            {wine.grape}
          </div>
        </Panel>
      </div>

      {/* Band 3 — Footer */}
      <div style={{ padding: `0 0 ${space.xs}` }}>
        <RuleDouble color={INK} opacity={0.45} />
      </div>

      <div
        style={{
          padding: `${space.sm} 0 ${space.md}`,
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: space.md,
          alignItems: 'start',
        }}
      >
        {/* Pairings */}
        <div>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.micro,
              letterSpacing: 3,
              textTransform: 'uppercase',
              color: INK_SOFT,
              marginBottom: 6,
            }}
          >
            At Table
          </div>
          {wine.pairs.map((p, i) => (
            <div
              key={i}
              style={{
                fontFamily: "'EB Garamond', serif",
                fontSize: typeScale.body,
                color: INK,
                lineHeight: lineHeight.body,
                display: 'flex',
                gap: 6,
                alignItems: 'baseline',
              }}
            >
              <span style={{ color: accent, fontSize: typeScale.micro }}>✦</span>
              {p}
            </div>
          ))}
        </div>

        {/* Drinking window */}
        <div>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.micro,
              letterSpacing: 3,
              textTransform: 'uppercase',
              color: INK_SOFT,
              marginBottom: 10,
            }}
          >
            Drinking Window
          </div>
          <DrinkingWindow drink={wine.drink} palette={wine.color} />
        </div>

        {/* Editor score + price */}
        <div style={{ textAlign: 'right' }}>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.micro,
              letterSpacing: 3,
              textTransform: 'uppercase',
              color: INK_SOFT,
              marginBottom: 2,
            }}
          >
            The Editor
          </div>
          {wine.critic.score > 0 ? (
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontStyle: 'italic',
                fontWeight: 500,
                fontSize: typeScale.display,
                color: OXBLOOD,
                lineHeight: lineHeight.tight,
              }}
            >
              {wine.critic.score}
              <span style={{ fontSize: typeScale.h3, opacity: 0.7, color: INK_SOFT }}>/100</span>
            </div>
          ) : (
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontStyle: 'italic',
                fontSize: typeScale.h2,
                color: INK_SOFT,
                lineHeight: lineHeight.tight,
              }}
            >
              N / R
            </div>
          )}
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: typeScale.body,
              color: INK,
              marginTop: 4,
            }}
          >
            {wine.price != null ? `$${wine.price}` : '—'}
            {' · '}
            {wine.abv}%
          </div>
        </div>
      </div>

      {/* Nav strip */}
      <div
        style={{
          padding: `0 0 ${space.lg}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: space.sm,
          flexWrap: 'wrap',
        }}
      >
        <button style={ghostBtn} onClick={() => navigate('/flight')}>
          ← The Flight
        </button>
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.label,
            color: INK_SOFT,
          }}
        >
          {wine.confidence} confidence · {wine.fits?.length ?? 0} profile markers
        </div>
        <button
          style={{ ...ghostBtn, background: INK, color: PAPER }}
          onClick={() => navigate(`/compare?a=${wineId}&b=wine-${wine.rank === 1 ? 2 : 1}`)}
        >
          Compare ⇆
        </button>
      </div>
    </PaperFrame>
  );
}
