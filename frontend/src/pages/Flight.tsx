import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import ListEntry from '@/components/Flight/ListEntry';
import StructureComparison from '@/components/Flight/StructureComparison';
import { INK, INK_SOFT, PAPER, RULE, lineHeight, space, typeScale } from '@/design/tokens';
import { enrichWine } from '@/design/wineColor';
import { useRecommendations } from '@/state/recommendationStore';
import type { RecommendationResponse, ProfileSummaryResponse } from '@/client/types.gen';
import {
  patchFeedbackHistoryFlightIdFeedbackPatch,
  profileSummaryProfileSummaryGet,
  patchProfileProfilePatch,
} from '@/client/sdk.gen';

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

const primaryBtn: React.CSSProperties = {
  ...ghostBtn,
  background: INK,
  color: PAPER,
};

export default function Flight() {
  const location = useLocation();
  const navigate = useNavigate();
  const { recommendations, setRecommendations } = useRecommendations();

  // Hydrate context from router state if arriving fresh from Preferences
  const data = recommendations;

  type SortKey = 'match' | 'price' | 'food';
  const [sortKey, setSortKey] = useState<SortKey>('match');
  const [feedbackChip, setFeedbackChip] = useState<string | null>(null);
  const [profile, setProfile] = useState<ProfileSummaryResponse | null>(null);
  const [grapeAdded, setGrapeAdded] = useState(false);
  const [grapeCalloutDismissed, setGrapeCalloutDismissed] = useState(false);

  useEffect(() => {
    const stateData = (location.state as { recommendations?: RecommendationResponse } | null)
      ?.recommendations;
    if (stateData) {
      setRecommendations(stateData);
    }
  }, []);

  useEffect(() => {
    profileSummaryProfileSummaryGet().then(({ data }) => {
      if (data) setProfile(data);
    });
  }, []);

  useEffect(() => {
    if (!grapeAdded) return;
    const t = setTimeout(() => setGrapeCalloutDismissed(true), 3000);
    return () => clearTimeout(t);
  }, [grapeAdded]);

  const wines = useMemo(() => {
    const base = (data?.recommendations ?? []).map(enrichWine);
    if (sortKey === 'price') {
      return [...base].sort((a, b) => {
        if (a.price == null && b.price == null) return a.rank - b.rank;
        if (a.price == null) return 1;
        if (b.price == null) return -1;
        return a.price - b.price;
      });
    }
    if (sortKey === 'food') {
      return [...base].sort((a, b) => {
        const diff = (b.pairs?.length ?? 0) - (a.pairs?.length ?? 0);
        return diff !== 0 ? diff : a.rank - b.rank;
      });
    }
    return base;
  }, [data, sortKey]);

  if (!data) {
    return (
      <PaperFrame>
        <Masthead dateline="Three bottles composed for this evening" />
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
  const topWine = wines[0];
  const showGrapeCallout =
    (grapeAdded || (
      !grapeCalloutDismissed &&
      !!topWine?.grape &&
      !!profile &&
      !(profile.topVarietals ?? []).includes(topWine.grape)
    ));

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

  const handleFeedbackChip = async (chip: string) => {
    if (!data.flightId) return;
    await patchFeedbackHistoryFlightIdFeedbackPatch({
      path: { flight_id: data.flightId },
      body: { chip, recordedAt: Date.now() / 1000 },
    });
    setFeedbackChip(chip);
  };

  const handleAddGrape = async () => {
    if (!topWine?.grape || !profile) return;
    await patchProfileProfilePatch({
      body: { topVarietals: [...(profile.topVarietals ?? []), topWine.grape] },
    });
    setGrapeAdded(true);
  };

  return (
    <PaperFrame>
      <Masthead dateline="Three bottles composed for this evening" />

      {/* Sub-header row */}
      <div
        style={{
          padding: `${space.sm} 0`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          flexWrap: 'wrap',
          gap: space.xs,
        }}
      >
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.h2,
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
            fontSize: typeScale.label,
            letterSpacing: 2,
            textTransform: 'uppercase',
            color: INK_SOFT,
            flexWrap: 'wrap',
          }}
        >
          {(
            [
              { key: 'match', label: 'Best match' },
              { key: 'price', label: 'By price' },
              { key: 'food', label: 'Food first' },
            ] as { key: SortKey; label: string }[]
          ).map(({ key, label }, i) => (
            <span
              key={key}
              onClick={() => setSortKey(key)}
              style={{
                cursor: 'pointer',
                borderBottom: sortKey === key ? `1px solid ${INK}` : 'none',
                color: sortKey === key ? INK : INK_SOFT,
              }}
            >
              {i > 0 ? `· ${label}` : label}
            </span>
          ))}
        </div>
      </div>

      {/* Double rule */}
      <div style={{ paddingBottom: space.sm }}>
        <RuleDouble color={INK} opacity={0.55} />
      </div>

      {/* Wine list */}
      <div style={{ display: 'grid', gap: space.md }}>
        {wines.map((wine) => (
          <ListEntry key={wine.id} wine={wine} />
        ))}
      </div>

      {/* Profile match note */}
      {data.profileMatchSummary && (
        <div
          style={{
            padding: `${space.sm} 0 0`,
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.body,
            color: INK_SOFT,
            lineHeight: lineHeight.body,
            maxWidth: 600,
          }}
        >
          {data.profileMatchSummary}
        </div>
      )}

      <StructureComparison wines={wines} />

      {/* Grape callout */}
      {(showGrapeCallout && topWine) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: space.sm,
            flexWrap: 'wrap',
            marginTop: space.md,
            paddingTop: space.sm,
            borderTop: `1px solid ${RULE}`,
          }}
        >
          <div
            style={{
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.label,
              color: INK_SOFT,
            }}
          >
            {grapeAdded ? `${topWine.grape} added. ✓` : `Enjoying ${topWine.grape}?`}
          </div>
          {!grapeAdded && (
            <>
              <button
                style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: typeScale.label,
                  color: INK,
                  border: `1px solid ${RULE}`,
                  background: 'transparent',
                  padding: '4px 10px',
                  cursor: 'pointer',
                  borderRadius: 0,
                }}
                onClick={handleAddGrape}
              >
                Add to your profile
              </button>
              <button
                style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: typeScale.label,
                  color: INK,
                  border: `1px solid ${RULE}`,
                  background: 'transparent',
                  padding: '4px 10px',
                  cursor: 'pointer',
                  borderRadius: 0,
                }}
                onClick={() => setGrapeCalloutDismissed(true)}
              >
                Dismiss
              </button>
            </>
          )}
        </div>
      )}

      {/* Feedback chips */}
      {data.flightId && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: space.sm,
            flexWrap: 'wrap',
            marginTop: space.md,
          }}
        >
          {feedbackChip === null ? (
            <>
              <div
                style={{
                  fontFamily: "'EB Garamond', serif",
                  fontStyle: 'italic',
                  fontSize: typeScale.label,
                  color: INK_SOFT,
                }}
              >
                How was the flight?
              </div>
              {[
                { label: 'Too bold', value: 'too_bold' },
                { label: 'Over budget', value: 'over_budget' },
                { label: 'Off profile', value: 'off_profile' },
                { label: 'Perfect', value: 'perfect' },
              ].map(({ label, value }) => (
                <button
                  key={value}
                  style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: typeScale.label,
                    color: INK,
                    border: `1px solid ${RULE}`,
                    background: 'transparent',
                    padding: '4px 10px',
                    cursor: 'pointer',
                    borderRadius: 0,
                  }}
                  onClick={() => handleFeedbackChip(value)}
                >
                  {label}
                </button>
              ))}
            </>
          ) : (
            <div
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: typeScale.label,
                color: INK_SOFT,
              }}
            >
              Noted. Adjust your palate on the{' '}
              <span
                onClick={() => navigate('/profile')}
                style={{ textDecoration: 'underline', cursor: 'pointer' }}
              >
                Profile page
              </span>{' '}
              →
            </div>
          )}
        </div>
      )}

      {/* Footer action band — flows inline so layout adapts to viewport */}
      <div
        style={{
          marginTop: space.lg,
          marginBottom: space.md,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: space.sm,
          flexWrap: 'wrap',
        }}
      >
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.label,
            color: INK_SOFT,
          }}
        >
          Composed by the Editor · drawing from your cellar on file
        </div>
        <div style={{ display: 'flex', gap: space.xs, flexWrap: 'wrap' }}>
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
