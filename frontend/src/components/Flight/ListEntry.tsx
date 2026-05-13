import { useNavigate } from 'react-router-dom';
import type { EnrichedWine } from '@/design/wineColor';
import RegionMap from '@/design/atoms/RegionMap';
import StructureBars from '@/design/atoms/StructureBars';
import { INK, INK_SOFT } from '@/design/tokens';

interface ListEntryProps {
  wine: EnrichedWine;
}

export default function ListEntry({ wine }: ListEntryProps) {
  const navigate = useNavigate();
  const accent = wine.color.accent;

  return (
    <div
      onClick={() => navigate(`/detail/${wine.id}`)}
      style={{
        display: 'grid',
        gridTemplateColumns: '108px 1fr 180px',
        gap: 22,
        alignItems: 'stretch',
        paddingBottom: 16,
        borderBottom: `1px dotted ${INK}`,
        cursor: 'pointer',
      }}
    >
      {/* Column 1 — terroir cartouche (Direction B style) */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontWeight: 500,
            fontStyle: 'italic',
            fontSize: 24,
            color: accent,
            lineHeight: 1,
            letterSpacing: 1,
          }}
        >
          № {wine.rank.toString().padStart(2, '0')}
        </div>
        <div
          style={{
            width: 28,
            height: 0.5,
            background: INK,
            opacity: 0.5,
            margin: '6px 0',
          }}
        />
        <RegionMap
          country={wine.country}
          lat={wine.coords.lat}
          lon={wine.coords.lon}
          palette={wine.color}
          size={84}
        />
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            fontSize: 10,
            letterSpacing: 2,
            textTransform: 'uppercase',
            color: INK_SOFT,
            marginTop: -6,
          }}
        >
          {wine.region ?? wine.country}
        </div>
      </div>

      {/* Column 2 — editorial body */}
      <div>
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            fontSize: 10,
            letterSpacing: 3,
            textTransform: 'uppercase',
            color: accent,
            marginBottom: 2,
          }}
        >
          {wine.region} · {wine.appellation}
        </div>
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontWeight: 500,
            fontSize: 28,
            lineHeight: 1.0,
            color: INK,
            letterSpacing: -0.5,
          }}
        >
          {wine.name}
        </div>
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: 14,
            color: INK_SOFT,
            marginTop: 2,
          }}
        >
          {wine.producer} · {wine.vintage}
        </div>
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontSize: 12.5,
            color: INK,
            lineHeight: 1.45,
            marginTop: 8,
            maxWidth: '95%',
          }}
        >
          <span
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: 22,
              lineHeight: 0,
              position: 'relative',
              top: 4,
              marginRight: 2,
              color: accent,
              fontStyle: 'italic',
            }}
          >
            "
          </span>
          {wine.palate.split('. ')[0]}.
        </div>
        <div
          style={{
            marginTop: 8,
            display: 'flex',
            gap: 14,
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: 11,
            letterSpacing: 1,
            textTransform: 'uppercase',
            color: INK_SOFT,
            flexWrap: 'wrap',
          }}
        >
          {wine.fits.slice(0, 3).map((f, i) => (
            <span key={i}>
              <span style={{ color: accent, marginRight: 4 }}>✦</span>
              {f}
            </span>
          ))}
        </div>
      </div>

      {/* Column 3 — score / structure / price */}
      <div
        style={{
          display: 'grid',
          gridTemplateRows: 'auto 1fr auto',
          gap: 6,
          textAlign: 'right',
        }}
      >
        <div>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: 9,
              letterSpacing: 3,
              textTransform: 'uppercase',
              color: INK_SOFT,
            }}
          >
            The Editor
          </div>
          {wine.critic.score > 0 ? (
            <>
              <div
                style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontStyle: 'italic',
                  fontWeight: 500,
                  fontSize: 38,
                  color: accent,
                  lineHeight: 1,
                }}
              >
                {wine.critic.score}
                <span style={{ fontSize: 14, opacity: 0.7 }}>/100</span>
              </div>
              <div
                style={{
                  fontFamily: "'EB Garamond', serif",
                  fontStyle: 'italic',
                  fontSize: 11,
                  color: INK_SOFT,
                }}
              >
                per {wine.critic.source}
              </div>
            </>
          ) : (
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontStyle: 'italic',
                fontSize: 14,
                color: INK_SOFT,
                marginTop: 4,
              }}
            >
              —
            </div>
          )}
        </div>
        <div style={{ alignSelf: 'center' }}>
          <StructureBars
            bars={{ tannin: wine.bars.tannin, acidity: wine.bars.acidity, body: wine.bars.body }}
            palette={wine.color}
            compact
          />
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'baseline',
            gap: 10,
          }}
        >
          <span
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: 11,
              color: INK_SOFT,
            }}
          >
            cellar price
          </span>
          <span
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              fontSize: 22,
              color: INK,
            }}
          >
            {wine.price != null ? `$${wine.price}` : '—'}
          </span>
        </div>
      </div>
    </div>
  );
}
