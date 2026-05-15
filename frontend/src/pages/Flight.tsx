import { useEffect, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import ListEntry from '@/components/Flight/ListEntry';
import { INK, INK_SOFT, PAPER } from '@/design/tokens';
import { enrichWine } from '@/design/wineColor';
import { useRecommendations } from '@/state/recommendationStore';
import type { RecommendationResponse } from '@/client/types.gen';

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

const primaryBtn: React.CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: 12,
  letterSpacing: 2,
  textTransform: 'uppercase',
  padding: '8px 14px',
  background: INK,
  color: PAPER,
  border: `1px solid ${INK}`,
  cursor: 'pointer',
};

export default function Flight() {
  const location = useLocation();
  const navigate = useNavigate();
  const { recommendations, setRecommendations } = useRecommendations();

  // Hydrate context from router state if arriving fresh from Preferences
  useEffect(() => {
    const stateData = (location.state as { recommendations?: RecommendationResponse } | null)
      ?.recommendations;
    if (stateData) {
      setRecommendations(stateData);
    }
  }, []);

  const data = recommendations;

  const wines = useMemo(
    () => (data?.recommendations ?? []).map(enrichWine),
    [data],
  );

  if (!data) {
    return (
      <PaperFrame>
        <Masthead dateline="Three bottles composed for this evening" />
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
          No recommendations found.{' '}
          <span
            onClick={() => navigate('/preferences')}
            style={{ textDecoration: 'underline', cursor: 'pointer' }}
          >
            Return to preferences.
          </span>
        </div>
      </PaperFrame>
    );
  }

  const topTwo = wines.slice(0, 2);

  const handleCompare = () => {
    if (topTwo.length >= 2) {
      navigate(`/compare?a=${topTwo[0].id}&b=${topTwo[1].id}`);
    }
  };

  const handleRecompose = () => {
    navigate('/preferences');
  };

  const handleNewWineList = () => {
    navigate('/preferences', { state: { sourceMode: 'winelist' } });
  };

  return (
    <PaperFrame>
      <Masthead dateline="Three bottles composed for this evening" />

      {/* Sub-header row */}
      <div
        style={{
          padding: '20px 44px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
        }}
      >
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            fontSize: 22,
            color: INK,
          }}
        >
          The Flight
        </div>
        <div
          style={{
            display: 'flex',
            gap: 18,
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: 11,
            letterSpacing: 2,
            textTransform: 'uppercase',
            color: INK_SOFT,
          }}
        >
          <span style={{ borderBottom: `1px solid ${INK}` }}>Best match</span>
          <span>· By price</span>
          <span>· Food first</span>
        </div>
      </div>

      {/* Double rule */}
      <div style={{ padding: '0 44px 16px' }}>
        <RuleDouble color={INK} opacity={0.55} />
      </div>

      {/* Wine list */}
      <div style={{ display: 'grid', gap: 18, padding: '4px 44px' }}>
        {wines.map((wine) => (
          <ListEntry key={wine.id} wine={wine} />
        ))}
      </div>

      {/* Profile match note */}
      {data.profileMatchSummary && (
        <div
          style={{
            padding: '16px 44px 0',
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: 12,
            color: INK_SOFT,
            maxWidth: 600,
          }}
        >
          {data.profileMatchSummary}
        </div>
      )}

      {/* Footer action band */}
      <div
        style={{
          position: 'absolute',
          left: 44,
          right: 44,
          bottom: 56,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: 12,
            color: INK_SOFT,
          }}
        >
          Composed by the Editor · drawing from your cellar on file
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button style={ghostBtn} onClick={handleNewWineList}>
            New wine list
          </button>
          <button style={ghostBtn} onClick={handleRecompose}>
            ↻ Recompose
          </button>
          {topTwo.length >= 2 && (
            <button style={primaryBtn} onClick={handleCompare}>
              Side by side ⇆
            </button>
          )}
        </div>
      </div>
    </PaperFrame>
  );
}
