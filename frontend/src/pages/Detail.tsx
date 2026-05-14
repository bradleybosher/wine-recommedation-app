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
import { INK, INK_SOFT, PAPER } from '@/design/tokens';
import { enrichWine } from '@/design/wineColor';
import { useRecommendations } from '@/state/recommendationStore';

const ghostBtn: React.CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: 12,
  letterSpacing: 2,
  textTransform: 'uppercase',
  padding: '8px 14px',
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
            padding: '60px 44px',
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: 16,
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
          padding: '26px 40px 14px',
          display: 'grid',
          gridTemplateColumns: '1fr 1.6fr',
          gap: 24,
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
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: 10,
              letterSpacing: 2,
              textTransform: 'uppercase',
              color: INK_SOFT,
              textAlign: 'center',
            }}
          >
            in the glass — {wine.color.glass}
          </div>
        </div>

        {/* Right — editorial body */}
        <div>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: 10,
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
              fontSize: 56,
              lineHeight: 0.92,
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
              fontSize: 20,
              color: INK_SOFT,
              marginBottom: 14,
            }}
          >
            {wine.producer} · {wine.vintage}
          </div>

          {/* Two-column body with drop cap */}
          <div
            style={{
              columns: 2,
              columnGap: 22,
              fontFamily: "'EB Garamond', serif",
              fontSize: 13,
              lineHeight: 1.55,
              color: INK,
            }}
          >
            <span
              style={{
                float: 'left',
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 56,
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
      <div style={{ padding: '10px 40px 0' }}>
        <RuleDouble color={INK} opacity={0.45} />
      </div>

      {/* Band 2 — Triptych */}
      <div
        style={{
          padding: '20px 40px 24px',
          display: 'grid',
          gridTemplateColumns: '1fr 1px 1fr 1px 1fr',
          gap: 0,
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
              fontSize: 12,
              color: INK_SOFT,
              textAlign: 'center',
              maxWidth: 180,
            }}
          >
            {wine.nose}
          </div>
        </Panel>

        {/* Vertical rule */}
        <div style={{ background: INK, opacity: 0.15 }} />

        {/* StructureBars panel */}
        <Panel title="Structure" caption="Palate">
          <div style={{ width: '100%', padding: '0 14px' }}>
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

        {/* Vertical rule */}
        <div style={{ background: INK, opacity: 0.15 }} />

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
              fontSize: 13,
              color: INK_SOFT,
              textAlign: 'center',
            }}
          >
            {wine.grape}
          </div>
        </Panel>
      </div>

      {/* Band 3 — Footer */}
      <div style={{ padding: '0 40px 6px' }}>
        <RuleDouble color={INK} opacity={0.45} />
      </div>

      <div
        style={{
          padding: '14px 40px 48px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: 24,
          alignItems: 'start',
        }}
      >
        {/* Pairings */}
        <div>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: 10,
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
                fontSize: 13,
                color: INK,
                lineHeight: 1.5,
                display: 'flex',
                gap: 6,
                alignItems: 'baseline',
              }}
            >
              <span style={{ color: accent, fontSize: 10 }}>✦</span>
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
              fontSize: 10,
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
              fontSize: 10,
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
                fontSize: 56,
                color: accent,
                lineHeight: 1,
              }}
            >
              {wine.critic.score}
              <span style={{ fontSize: 18, opacity: 0.7 }}>/100</span>
            </div>
          ) : (
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontStyle: 'italic',
                fontSize: 28,
                color: INK_SOFT,
                lineHeight: 1,
              }}
            >
              N / R
            </div>
          )}
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: 14,
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
          position: 'absolute',
          left: 40,
          right: 40,
          bottom: 20,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <button style={ghostBtn} onClick={() => navigate('/flight')}>
          ← The Flight
        </button>
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: 11,
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
