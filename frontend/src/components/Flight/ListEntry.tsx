import { useNavigate } from 'react-router-dom';
import type { EnrichedWine } from '@/design/wineColor';
import RegionMap from '@/design/atoms/RegionMap';
import StructureBars from '@/design/atoms/StructureBars';
import WineTypeLabel from '@/design/atoms/WineTypeLabel';
import { INK, INK_SOFT, OXBLOOD, lineHeight, space, typeScale } from '@/design/tokens';

interface ListEntryProps {
  wine: EnrichedWine;
}

export default function ListEntry({ wine }: ListEntryProps) {
  const navigate = useNavigate();
  const accent = wine.color.accent;
  // Rank ordinality must read independent of palette hue (colour-blind safe);
  // accent stays for decorative cues only (region label, food-fit pips).
  const rankColor = wine.rank === 1 ? OXBLOOD : INK;

  return (
    <div
      onClick={() => navigate(`/detail/${wine.id}`)}
      className="flight-entry-grid"
      style={{
        containerType: 'inline-size',
        display: 'grid',
        gridTemplateColumns: 'minmax(96px, 0.5fr) minmax(0, 2.4fr) minmax(140px, 0.9fr)',
        gap: space.md,
        alignItems: 'stretch',
        paddingBottom: space.sm,
        borderBottom: `1px dotted ${INK}`,
        cursor: 'pointer',
      }}
    >
      {/* Column 1 — terroir cartouche */}
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
            fontSize: typeScale.h2,
            color: rankColor,
            lineHeight: lineHeight.tight,
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
            fontSize: typeScale.micro,
            letterSpacing: 2,
            textTransform: 'uppercase',
            color: INK_SOFT,
            marginTop: -6,
          }}
        >
          {wine.region ?? wine.country}
        </div>
        <WineTypeLabel palette={wine.color} grape={wine.grape} style={{ marginTop: 4 }} />
      </div>

      {/* Column 2 — editorial body */}
      <div>
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.micro,
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
            fontSize: typeScale.h1,
            lineHeight: lineHeight.tight,
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
            fontSize: typeScale.body,
            color: INK_SOFT,
            marginTop: 2,
          }}
        >
          {wine.producer} · {wine.vintage}
        </div>
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontSize: typeScale.body,
            color: INK,
            lineHeight: lineHeight.body,
            marginTop: 8,
            maxWidth: '95%',
          }}
        >
          <span
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: typeScale.h3,
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
            fontSize: typeScale.label,
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
        className="flight-entry-score"
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
              fontSize: typeScale.micro,
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
                  fontSize: typeScale.h1,
                  color: INK,
                  lineHeight: lineHeight.tight,
                }}
              >
                {wine.critic.score}
                <span style={{ fontSize: typeScale.body, opacity: 0.7 }}>/100</span>
              </div>
              <div
                style={{
                  fontFamily: "'EB Garamond', serif",
                  fontStyle: 'italic',
                  fontSize: typeScale.label,
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
                fontSize: typeScale.body,
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
              fontSize: typeScale.label,
              color: INK_SOFT,
            }}
          >
            cellar price
          </span>
          <span
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              fontSize: typeScale.h3,
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
