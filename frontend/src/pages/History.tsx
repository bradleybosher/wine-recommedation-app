import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import { INK, INK_SOFT, RULE } from '@/design/tokens';
import { listHistoryHistoryGet, getHistoryHistoryFlightIdGet } from '@/client';
import { useRecommendations } from '@/state/recommendationStore';
import type { FlightSummary } from '@/client/types.gen';

const ghostBtn: React.CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: 11,
  letterSpacing: 2,
  textTransform: 'uppercase',
  padding: '6px 12px',
  background: 'transparent',
  color: INK,
  border: `1px solid ${INK}`,
  cursor: 'pointer',
};

export default function History() {
  const navigate = useNavigate();
  const { setRecommendations } = useRecommendations();

  const [flights, setFlights] = useState<FlightSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [loadingId, setLoadingId] = useState<string | null>(null);

  useEffect(() => {
    listHistoryHistoryGet()
      .then((r) => setFlights(Array.isArray(r.data) ? r.data : []))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load history'))
      .finally(() => setLoading(false));
  }, []);

  const handleLoad = async (id: string) => {
    setLoadingId(id);
    try {
      const r = await getHistoryHistoryFlightIdGet({ path: { flight_id: id } });
      if (r.data) {
        setRecommendations(r.data.response);
        navigate('/flight');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load flight');
      setLoadingId(null);
    }
  };

  const today = new Date().toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' });

  return (
    <PaperFrame>
      <Masthead dateline={`Tasting Notes Archive · ${today}`} />

      {/* Nav row */}
      <div style={{ padding: '10px 44px 0', display: 'flex', justifyContent: 'flex-end' }}>
        <Link
          to="/preferences"
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            fontSize: 11,
            letterSpacing: 3,
            textTransform: 'uppercase',
            color: INK_SOFT,
            textDecoration: 'none',
            borderBottom: `1px solid ${INK_SOFT}`,
            paddingBottom: 1,
          }}
        >
          New composition
        </Link>
      </div>

      {/* Header */}
      <div style={{ padding: '20px 44px 4px' }}>
        <div style={{ fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic', fontSize: 26, color: INK, lineHeight: 1 }}>
          Past Flights
        </div>
      </div>
      <div style={{ padding: '10px 44px 16px' }}>
        <RuleDouble color={INK} opacity={0.45} />
      </div>

      {/* Column headers */}
      {!loading && flights.length > 0 && (
        <div
          style={{
            padding: '0 44px 8px',
            display: 'grid',
            gridTemplateColumns: '72px 1fr 1fr 96px',
            gap: 16,
            alignItems: 'baseline',
          }}
        >
          {['Date', 'Occasion', 'Lead wine', ''].map((h) => (
            <span
              key={h}
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 9,
                letterSpacing: 3,
                textTransform: 'uppercase',
                color: INK_SOFT,
              }}
            >
              {h}
            </span>
          ))}
        </div>
      )}

      {/* Body */}
      <div style={{ padding: '0 44px 80px' }}>
        {loading && (
          <div style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: 15, color: INK_SOFT, paddingTop: 40, textAlign: 'center' }}>
            Loading…
          </div>
        )}

        {!loading && error && (
          <div style={{ fontFamily: "'EB Garamond', serif", fontSize: 14, color: '#c0392b', paddingTop: 24 }}>
            {error}
          </div>
        )}

        {!loading && !error && flights.length === 0 && (
          <div
            style={{
              paddingTop: 60,
              textAlign: 'center',
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: 16,
              color: INK_SOFT,
            }}
          >
            No flights on record yet.{' '}
            <span
              onClick={() => navigate('/preferences')}
              style={{ textDecoration: 'underline', cursor: 'pointer' }}
            >
              Compose the first.
            </span>
          </div>
        )}

        {!loading && flights.map((flight, i) => {
          const date = new Date(flight.createdAt * 1000);
          const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          const isLast = i === flights.length - 1;

          return (
            <div
              key={flight.id}
              style={{
                display: 'grid',
                gridTemplateColumns: '72px 1fr 1fr 96px',
                gap: 16,
                alignItems: 'center',
                padding: '12px 0',
                borderBottom: isLast ? 'none' : `1px solid ${RULE}`,
              }}
            >
              <span style={{ fontFamily: "'EB Garamond', serif", fontSize: 13, color: INK_SOFT }}>
                {dateStr}
              </span>
              <span style={{ fontFamily: "'EB Garamond', serif", fontSize: 14, color: INK }}>
                {flight.occasion || '—'}
                {flight.menu && (
                  <span style={{ color: INK_SOFT, fontSize: 12 }}>{' · '}{flight.menu}</span>
                )}
              </span>
              <span style={{ fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic', fontSize: 15, color: INK }}>
                {flight.topWineName}
              </span>
              <button
                style={{ ...ghostBtn, opacity: loadingId === flight.id ? 0.5 : 1 }}
                disabled={loadingId !== null}
                onClick={() => handleLoad(flight.id)}
              >
                {loadingId === flight.id ? '…' : 'View'}
              </button>
            </div>
          );
        })}
      </div>
    </PaperFrame>
  );
}
