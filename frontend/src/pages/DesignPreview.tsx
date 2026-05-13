import PaperFrame from '@/design/PaperFrame';
import Field from '@/design/Field';
import Masthead from '@/design/atoms/Masthead';
import FlavorWheel from '@/design/atoms/FlavorWheel';
import StructureBars from '@/design/atoms/StructureBars';
import RegionMap from '@/design/atoms/RegionMap';
import GlassPour from '@/design/atoms/GlassPour';
import Bottle from '@/design/atoms/Bottle';
import Fleuron from '@/design/atoms/Fleuron';
import RuleDouble from '@/design/atoms/RuleDouble';
import DrinkingWindow from '@/design/atoms/DrinkingWindow';
import { PALETTES, INK, INK_SOFT, OXBLOOD } from '@/design/tokens';

const WINES = [
  {
    id: 'brunello',
    name: 'Brunello di Montalcino',
    producer: 'Biondi-Santi',
    vintage: 2016,
    region: 'Tuscany',
    country: 'Italy',
    appellation: 'Montalcino · DOCG',
    coords: { lat: 43.05, lon: 11.49 },
    grape: 'Sangiovese (Brunello clone)',
    price: 185,
    abv: 14.5,
    drink: { from: 2024, peak: 2030, until: 2042 },
    color: PALETTES.brunello,
    bars: { tannin: 8, acidity: 7, body: 8, sweetness: 1, oak: 6 },
    wheel: { 'Dried Cherry': 9, 'Leather': 6, 'Tobacco': 5, 'Earth': 8, 'Violet': 4, 'Plum': 6, 'Anise': 3, 'Forest Floor': 7 },
    nose: 'dried cherry · leather · tobacco · forest floor',
    palate: 'A structured Sangiovese that mirrors the savoury, dried-cherry profile your cellar leans on.',
    pairs: ['Bistecca alla Fiorentina', 'Aged pecorino', 'Wild boar ragù'],
    critic: { score: 96, source: 'Galloni' },
  },
  {
    id: 'chablis',
    name: 'Chablis Grand Cru "Les Clos"',
    producer: 'Domaine William Fèvre',
    vintage: 2020,
    region: 'Burgundy',
    country: 'France',
    appellation: 'Chablis Grand Cru',
    coords: { lat: 47.81, lon: 3.80 },
    grape: 'Chardonnay',
    price: 135,
    abv: 13.0,
    drink: { from: 2024, peak: 2028, until: 2035 },
    color: PALETTES.chablis,
    bars: { tannin: 1, acidity: 9, body: 6, sweetness: 1, oak: 3 },
    wheel: { 'Lemon Zest': 8, 'Oyster Shell': 9, 'Green Apple': 7, 'Flint': 8, 'White Flower': 5, 'Beeswax': 4, 'Almond': 4, 'Chalk': 8 },
    nose: 'lemon zest · oyster shell · flint · chalk',
    palate: 'A taut, chiselled Chablis with Kimmeridgian salinity.',
    pairs: ['Plateau de fruits de mer', 'Beurre blanc turbot', 'Comté affiné'],
    critic: { score: 94, source: 'Burghound' },
  },
];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 48 }}>
      <div style={{ fontSize: 9, letterSpacing: 4, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 12 }}>{title}</div>
      <RuleDouble />
      <div style={{ marginTop: 20 }}>{children}</div>
    </div>
  );
}

export default function DesignPreview() {
  return (
    <PaperFrame>
      <Masthead />

      <div style={{ padding: '32px 44px', maxWidth: 900, margin: '0 auto' }}>
        <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 11, letterSpacing: 3, textTransform: 'uppercase', color: OXBLOOD, marginBottom: 8 }}>
          Design Preview — Phase 1 Atoms
        </div>

        {/* Masthead variants */}
        <Section title="Masthead">
          <div style={{ display: 'grid', gap: 24 }}>
            <div>
              <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>Large (default)</div>
              <Masthead />
            </div>
            <div>
              <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>Small variant</div>
              <Masthead small dateline="Cellar Review · Spring" />
            </div>
          </div>
        </Section>

        {/* RuleDouble */}
        <Section title="Rule Double">
          <RuleDouble />
        </Section>

        {/* Fleuron */}
        <Section title="Fleuron">
          <div style={{ display: 'flex', gap: 32, alignItems: 'center' }}>
            <Fleuron />
            <Fleuron size={16} />
            <Fleuron size={36} color={OXBLOOD} />
          </div>
        </Section>

        {/* Field */}
        <Section title="Field">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, maxWidth: 600 }}>
            <Field label="Occasion" value="Anniversary supper, four guests" />
            <Field label="Menu" value="Charred ribeye · porcini · Roquefort" />
            <Field label="Cellar leans toward" value="Sangiovese · Nebbiolo · old-world reds" inkAccent />
            <Field label="Temperament" value="Adventurous, within reason" />
            <Field label="Ceiling" value="$200" small />
            <Field label="Bottles" value="3 selections" small />
          </div>
        </Section>

        {/* Per-wine atoms */}
        {WINES.map((wine) => (
          <div key={wine.id}>
            <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 22, fontWeight: 500, color: wine.color.accent, marginBottom: 4 }}>
              {wine.name}
            </div>
            <div style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: 13, color: INK_SOFT, marginBottom: 24 }}>
              {wine.producer} · {wine.vintage} · {wine.appellation}
            </div>

            <Section title="Flavor Wheel">
              <div style={{ display: 'flex', gap: 48, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>size=210</div>
                  <FlavorWheel data={wine.wheel} size={210} palette={wine.color} />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>size=140, no labels</div>
                  <FlavorWheel data={wine.wheel} size={140} palette={wine.color} label={false} />
                </div>
              </div>
            </Section>

            <Section title="Structure Bars">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 40 }}>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>Full (all 5)</div>
                  <StructureBars bars={wine.bars} palette={wine.color} />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>Compact (tannin/acidity/body)</div>
                  <StructureBars bars={wine.bars} palette={wine.color} labels={['tannin', 'acidity', 'body']} compact />
                </div>
              </div>
            </Section>

            <Section title="Region Map">
              <div style={{ display: 'flex', gap: 40, alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>size=150 with label</div>
                  <RegionMap country={wine.country} lat={wine.coords.lat} lon={wine.coords.lon} label={wine.appellation} palette={wine.color} size={150} />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>size=84 (flight cartouche)</div>
                  <RegionMap country={wine.country} lat={wine.coords.lat} lon={wine.coords.lon} palette={wine.color} size={84} />
                </div>
              </div>
            </Section>

            <Section title="Glass Pour">
              <div style={{ display: 'flex', gap: 32, alignItems: 'flex-end' }}>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>fill=0.55</div>
                  <GlassPour palette={wine.color} size={86} fill={0.55} />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>fill=0.3</div>
                  <GlassPour palette={wine.color} size={86} fill={0.3} />
                </div>
              </div>
            </Section>

            <Section title="Bottle">
              <div style={{ display: 'flex', gap: 40, alignItems: 'flex-end' }}>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>Bordeaux</div>
                  <Bottle palette={wine.color} shape="bordeaux" size={68} />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>Burgundy</div>
                  <Bottle palette={wine.color} shape="burgundy" size={68} />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: INK_SOFT, marginBottom: 8, fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>small (36)</div>
                  <Bottle palette={wine.color} size={36} />
                </div>
              </div>
            </Section>

            <Section title="Drinking Window">
              <div style={{ maxWidth: 400 }}>
                <DrinkingWindow drink={wine.drink} palette={wine.color} />
              </div>
            </Section>

            <div style={{ marginBottom: 48 }}>
              <RuleDouble />
            </div>
          </div>
        ))}
      </div>
    </PaperFrame>
  );
}
