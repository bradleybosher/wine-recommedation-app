import { useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import FlavorWheel from '@/design/atoms/FlavorWheel';
import StructureBars from '@/design/atoms/StructureBars';
import Bottle from '@/design/atoms/Bottle';
import { INK, INK_SOFT, PAPER } from '@/design/tokens';
import { enrichWine } from '@/design/wineColor';
import { useRecommendations } from '@/state/recommendationStore';
import type { EnrichedWine } from '@/design/wineColor';

const ghostBtn: React.CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: 12,
  letterSpacing: 2,
  textTransform: 'uppercase',
  padding: '8px 14px',
  background: 'transparent',
  color: PAPER,
  border: `1px solid ${PAPER}`,
  cursor: 'pointer',
  opacity: 0.7,
};

function WinePane({ wine, side }: { wine: EnrichedWine; side: 'left' | 'right' }) {
  const eyebrow = side === 'left' ? 'À gauche' : 'À droite';
  const isWhite = wine.color.glass.startsWith('#d') || wine.color.glass.startsWith('#c');
  const bottleShape = wine.appellation?.toLowerCase().includes('burgundy') ||
    wine.appellation?.toLowerCase().includes('bourgogne') ||
    wine.appellation?.toLowerCase().includes('chablis')
    ? 'burgundy'
    : 'bordeaux';

  const barsRecord: Record<string, number> = {
    tannin: wine.bars.tannin,
    acidity: wine.bars.acidity,
    body: wine.bars.body,
    sweetness: wine.bars.sweetness,
    oak: wine.bars.oak,
  };

  const palateSnippet = wine.palate.split('. ')[0] ?? wine.palate;
  const hasScore = wine.critic.score > 0;

  return (
    <div
      style={{
        padding: '22px 28px',
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
        position: 'relative',
        minHeight: 0,
      }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: 10,
              letterSpacing: 3,
              textTransform: 'uppercase',
              color: wine.color.accent,
            }}
          >
            {eyebrow} · {wine.appellation}
          </div>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: 28,
              lineHeight: 1,
              color: INK,
              marginTop: 2,
              letterSpacing: -0.5,
            }}
          >
            {wine.name}
          </div>
          <div
            style={{
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: 13,
              color: INK_SOFT,
              marginTop: 2,
            }}
          >
            {wine.producer} · {wine.vintage}
          </div>
        </div>
        <div style={{ flexShrink: 0, marginLeft: 12 }}>
          <Bottle palette={wine.color} shape={bottleShape} size={36} />
        </div>
      </div>

      {/* Flavor wheel */}
      <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 4 }}>
        <FlavorWheel data={wine.wheel} palette={wine.color} size={170} />
      </div>

      {/* Structure bars */}
      <StructureBars bars={barsRecord} palette={wine.color} />

      {/* Palate pull-quote */}
      <div
        style={{
          fontFamily: "'EB Garamond', serif",
          fontSize: 12.5,
          lineHeight: 1.55,
          color: INK,
        }}
      >
        <span
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            color: wine.color.accent,
          }}
        >
          "
        </span>
        {palateSnippet}.{' '}
        <span
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            color: wine.color.accent,
          }}
        >
          "
        </span>
      </div>

      {/* Bottom row: score + price / peak */}
      <div
        style={{
          marginTop: 'auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
        }}
      >
        <span
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontWeight: 500,
            fontSize: 32,
            color: wine.color.accent,
          }}
        >
          {hasScore ? wine.critic.score : '—'}
          {wine.price && (
            <span style={{ fontSize: 12, color: INK_SOFT, opacity: 0.7 }}> · ${wine.price}</span>
          )}
        </span>
        <span
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            fontSize: 12,
            color: INK_SOFT,
          }}
        >
          peak {wine.drink.peak}
        </span>
      </div>
    </div>
  );
}

export default function Compare() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { recommendations } = useRecommendations();

  const aId = params.get('a');
  const bId = params.get('b');

  const allWines = useMemo(
    () => (recommendations?.recommendations ?? []).map(enrichWine),
    [recommendations],
  );

  const wineA = useMemo(() => allWines.find((w) => w.id === aId) ?? allWines[0], [allWines, aId]);
  const wineB = useMemo(
    () => allWines.find((w) => w.id === bId) ?? allWines[1],
    [allWines, bId],
  );

  if (!wineA || !wineB) {
    return (
      <PaperFrame>
        <Masthead small dateline="A comparative tasting · two bottles, one table" />
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
          No wines to compare.{' '}
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

  const nameA = wineA.name.split(' ').slice(0, 2).join(' ');
  const nameB = wineB.name.split(' ').slice(0, 2).join(' ');

  return (
    <PaperFrame>
      <Masthead small dateline="A comparative tasting · two bottles, one table" />

      {/* Two-column body */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1px 1fr',
          flex: 1,
          minHeight: 0,
          paddingBottom: 130,
        }}
      >
        <WinePane wine={wineA} side="left" />

        {/* Vertical hairline rule */}
        <div style={{ background: INK, opacity: 0.4 }} />

        <WinePane wine={wineB} side="right" />
      </div>

      {/* Nav strip */}
      <div
        style={{
          position: 'absolute',
          left: 44,
          bottom: 100,
          display: 'flex',
          gap: 12,
        }}
      >
        <button style={ghostBtn} onClick={() => navigate('/flight')}>
          ← The Flight
        </button>
      </div>

      {/* Verdict band */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          padding: '14px 40px 44px',
          background: INK,
          color: PAPER,
        }}
      >
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            fontSize: 9,
            letterSpacing: 4,
            textTransform: 'uppercase',
            opacity: 0.7,
          }}
        >
          The Editor's Verdict
        </div>
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: 18,
            lineHeight: 1.35,
            marginTop: 4,
            fontStyle: 'italic',
          }}
        >
          "Open the{' '}
          <span style={{ color: wineA.color.tint }}>{nameA}</span> first — it is generous tonight;
          pour the{' '}
          <span style={{ color: wineB.color.tint }}>{nameB}</span> with the second course, decanted
          ninety minutes."
        </div>
      </div>
    </PaperFrame>
  );
}
