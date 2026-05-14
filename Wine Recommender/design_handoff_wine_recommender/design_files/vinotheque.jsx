// Variation A — "Vinothèque"
// A Wine Spectator-style editorial magazine. Cream paper, oxblood ink,
// Cormorant display + EB Garamond body. Each wine is a magazine cover spread.

const { useState: useStateA } = React;

const PAPER = '#f3e8d4';
const PAPER_DEEP = '#ecdfc4';
const INK = '#1f120a';
const INK_SOFT = '#3a261b';
const RULE = 'rgba(31,18,10,0.5)';
const OXBLOOD = '#5e1418';

const serifDisp = "'Cormorant Garamond', 'Cormorant', serif";
const serifBody = "'EB Garamond', 'Cormorant Garamond', serif";

// ─── Frame: a piece of cream paper with deckled edges + slight tone shift
function PaperFrame({ children, w, h, label, no, tint }) {
  return (
    <div style={{
      width: w, height: h, position: 'relative',
      background: tint ? `linear-gradient(${PAPER} 0%, ${PAPER} 60%, ${tint} 100%)` : PAPER,
      color: INK, fontFamily: serifBody,
      overflow: 'hidden',
      boxShadow: 'inset 0 0 80px rgba(80,40,10,0.06)',
    }}>
      {/* paper texture noise */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        backgroundImage: 'radial-gradient(rgba(80,40,10,0.025) 1px, transparent 1px)',
        backgroundSize: '3px 3px',
        mixBlendMode: 'multiply',
      }} />
      {/* edge */}
      <div style={{
        position: 'absolute', inset: 0, border: '1px solid rgba(80,40,10,0.12)', pointerEvents: 'none',
      }} />
      {children}
      {/* folio number */}
      {no && (
        <div style={{
          position: 'absolute', bottom: 14, left: '50%', transform: 'translateX(-50%)',
          fontFamily: serifDisp, fontStyle: 'italic', fontSize: 11, color: INK, opacity: 0.6, letterSpacing: 2,
        }}>· {no} ·</div>
      )}
      {label && (
        <div style={{
          position: 'absolute', top: 14, right: 16, fontFamily: serifDisp, fontStyle: 'italic',
          fontSize: 10, letterSpacing: 3, textTransform: 'uppercase', color: INK_SOFT, opacity: 0.7,
        }}>{label}</div>
      )}
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Masthead used at top of pages
function Masthead({ small, dateline }) {
  return (
    <div style={{ padding: small ? '18px 32px 12px' : '28px 40px 14px', textAlign: 'center', borderBottom: `2px solid ${INK}` }}>
      <div style={{ fontFamily: serifDisp, fontSize: 10, letterSpacing: 6, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 6 }}>
        Volume XII · Number IV
      </div>
      <div style={{ fontFamily: serifDisp, fontWeight: 500, fontSize: small ? 36 : 56, letterSpacing: -1, lineHeight: 0.95, color: INK }}>
        Vinothèque
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 8 }}>
        <div style={{ fontFamily: serifBody, fontStyle: 'italic', fontSize: 11, color: INK_SOFT }}>{dateline || 'A Private Cellar Review'}</div>
        <div style={{ fontFamily: serifDisp, fontSize: 10, letterSpacing: 3, textTransform: 'uppercase', color: INK_SOFT }}>Est. MMXIV</div>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// A · Preferences page — intake form styled as a magazine subscription card
function VinPreferences({ w, h }) {
  return (
    <PaperFrame w={w} h={h} no="I" label="Folio · The Intake">
      <Masthead dateline="Issue prepared for one guest · 13 May" />
      <div style={{ padding: '24px 44px', display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: 36 }}>
        <div>
          <div style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 14, color: INK_SOFT, marginBottom: 6 }}>The Editor inquires:</div>
          <div style={{ fontFamily: serifDisp, fontSize: 44, lineHeight: 0.96, letterSpacing: -1, color: INK }}>
            What will <span style={{ fontStyle: 'italic' }}>you</span> open<br />tonight?
          </div>
          <div style={{ marginTop: 14, fontFamily: serifBody, fontSize: 13, lineHeight: 1.55, color: INK_SOFT, fontStyle: 'italic' }}>
            Provide a few particulars — the meal, the company, the temperament of the evening — and our cellar editor will compose a flight from your collection and the houses we admire.
          </div>
          <div style={{ marginTop: 22 }}><Fleuron color={INK} size={20} /></div>
        </div>
        <div style={{ display: 'grid', gap: 18 }}>
          <Field label="Occasion" value="Anniversary supper, four guests" />
          <Field label="Menu" value="Charred ribeye · porcini · Roquefort" />
          <Field label="Cellar leans toward" value="Sangiovese · Nebbiolo · old-world reds" inkAccent />
          <Field label="Temperament" value="Adventurous, within reason" />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <Field label="Ceiling" value="$200" small />
            <Field label="Bottles" value="3 selections" small />
          </div>
          <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontFamily: serifBody, fontStyle: 'italic', fontSize: 12, color: INK_SOFT }}>
              ✦ The editor will draw from 412 bottles on file
            </div>
            <button style={{
              fontFamily: serifDisp, fontSize: 14, letterSpacing: 3, textTransform: 'uppercase',
              padding: '10px 22px', background: INK, color: PAPER, border: 'none', cursor: 'pointer',
            }}>
              Compose the flight →
            </button>
          </div>
        </div>
      </div>
      {/* lower band — what the issue will contain */}
      <div style={{ position: 'absolute', left: 44, right: 44, bottom: 56 }}>
        <RuleDouble color={INK} opacity={0.45} />
        <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 18, fontFamily: serifBody }}>
          {[
            ['I.', 'The Intake', 'Particulars of the evening'],
            ['II.', 'Three Reviews', 'Composed for the night'],
            ['III.', 'The Estate', 'Profile of a bottle'],
            ['IV.', 'Side by Side', 'A comparative tasting'],
          ].map(([n, t, s]) => (
            <div key={n} style={{ textAlign: 'left' }}>
              <div style={{ fontFamily: serifDisp, fontSize: 18, fontStyle: 'italic', color: OXBLOOD }}>{n}</div>
              <div style={{ fontFamily: serifDisp, fontWeight: 500, fontSize: 15, color: INK, letterSpacing: 0.2 }}>{t}</div>
              <div style={{ fontStyle: 'italic', fontSize: 11, color: INK_SOFT, marginTop: 2 }}>{s}</div>
            </div>
          ))}
        </div>
      </div>
    </PaperFrame>
  );
}

function Field({ label, value, small, inkAccent }) {
  return (
    <div>
      <div style={{ fontFamily: serifDisp, fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', color: INK_SOFT, opacity: 0.85, marginBottom: 4 }}>{label}</div>
      <div style={{
        fontFamily: serifDisp, fontSize: small ? 18 : 22, color: inkAccent ? OXBLOOD : INK,
        borderBottom: `1px solid ${INK}`, paddingBottom: 4, fontStyle: inkAccent ? 'italic' : 'normal',
      }}>{value}</div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// A · Recommendations — magazine "contents" of three reviews stacked
function VinList({ w, h, wines }) {
  return (
    <PaperFrame w={w} h={h} no="II" label="Folio · The Flight">
      <Masthead dateline="Three bottles composed for this evening" />
      <div style={{ padding: '20px 44px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <div style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 22, color: INK }}>The Flight</div>
        <div style={{ display: 'flex', gap: 18, fontFamily: serifDisp, fontSize: 11, letterSpacing: 2, textTransform: 'uppercase', color: INK_SOFT }}>
          <span style={{ borderBottom: `1px solid ${INK}` }}>Under $200</span>
          <span>· More adventurous</span>
          <span>· Food first</span>
          <span>· The classics</span>
        </div>
      </div>
      <div style={{ padding: '0 44px 16px' }}>
        <RuleDouble color={INK} opacity={0.55} />
      </div>
      <div style={{ display: 'grid', gap: 18, padding: '4px 44px' }}>
        {wines.map((wine, i) => (
          <ListEntry key={wine.id} wine={wine} />
        ))}
      </div>
      {/* footer action */}
      <div style={{ position: 'absolute', left: 44, right: 44, bottom: 56, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontFamily: serifBody, fontStyle: 'italic', fontSize: 12, color: INK_SOFT }}>
          Composed by the Editor · drawing from 412 bottles on file
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button style={ghostBtn}>↻ Recompose</button>
          <button style={primaryBtn}>Side by side ⇆</button>
        </div>
      </div>
    </PaperFrame>
  );
}

const ghostBtn = {
  fontFamily: serifDisp, fontSize: 12, letterSpacing: 2, textTransform: 'uppercase',
  padding: '8px 14px', background: 'transparent', color: INK, border: `1px solid ${INK}`, cursor: 'pointer',
};
const primaryBtn = {
  fontFamily: serifDisp, fontSize: 12, letterSpacing: 2, textTransform: 'uppercase',
  padding: '8px 14px', background: INK, color: PAPER, border: `1px solid ${INK}`, cursor: 'pointer',
};

function ListEntry({ wine }) {
  const accent = wine.color.accent;
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '108px 1fr 180px', gap: 22, alignItems: 'stretch',
      paddingBottom: 16, borderBottom: `1px dotted ${INK}`,
    }}>
      {/* terroir cartouche — small editorial numeral + region map + appellation */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
        <div style={{
          fontFamily: serifDisp, fontWeight: 500, fontStyle: 'italic', fontSize: 24,
          color: accent, lineHeight: 1, letterSpacing: 1,
        }}>№ {wine.rank.toString().padStart(2, '0')}</div>
        <div style={{
          width: 28, height: 0.5, background: INK, opacity: 0.5, margin: '6px 0',
        }} />
        <RegionMap country={wine.country} lat={wine.coords.lat} lon={wine.coords.lon} palette={wine.color} size={84} />
        <div style={{
          fontFamily: serifDisp, fontStyle: 'italic', fontSize: 10, letterSpacing: 2,
          textTransform: 'uppercase', color: INK_SOFT, marginTop: -6,
        }}>{wine.region}</div>
      </div>
      <div>
        <div style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 10, letterSpacing: 3, textTransform: 'uppercase', color: accent, marginBottom: 2 }}>
          {wine.region} · {wine.appellation}
        </div>
        <div style={{ fontFamily: serifDisp, fontWeight: 500, fontSize: 28, lineHeight: 1.0, color: INK, letterSpacing: -0.5 }}>
          {wine.name}
        </div>
        <div style={{ fontFamily: serifBody, fontStyle: 'italic', fontSize: 14, color: INK_SOFT, marginTop: 2 }}>
          {wine.producer} · {wine.vintage}
        </div>
        <div style={{ fontFamily: serifBody, fontSize: 12.5, color: INK, lineHeight: 1.45, marginTop: 8, maxWidth: '95%' }}>
          <span style={{ fontFamily: serifDisp, fontSize: 22, lineHeight: 0, position: 'relative', top: 4, marginRight: 2, color: accent, fontStyle: 'italic' }}>"</span>
          {wine.palate.split('. ')[0]}.
        </div>
        <div style={{ marginTop: 8, display: 'flex', gap: 14, fontFamily: serifDisp, fontSize: 11, letterSpacing: 1, textTransform: 'uppercase', color: INK_SOFT }}>
          {wine.fits.slice(0, 3).map((f, i) => (
            <span key={i}>
              <span style={{ color: accent, marginRight: 4 }}>✦</span>{f}
            </span>
          ))}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateRows: 'auto 1fr auto', gap: 6, textAlign: 'right' }}>
        <div>
          <div style={{ fontFamily: serifDisp, fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', color: INK_SOFT }}>The Editor</div>
          <div style={{ fontFamily: serifDisp, fontStyle: 'italic', fontWeight: 500, fontSize: 38, color: accent, lineHeight: 1 }}>{wine.critic.score}<span style={{ fontSize: 14, opacity: 0.7 }}>/100</span></div>
          <div style={{ fontFamily: serifBody, fontStyle: 'italic', fontSize: 11, color: INK_SOFT }}>per {wine.critic.source}</div>
        </div>
        <div style={{ alignSelf: 'center' }}>
          <StructureBars bars={{ tannin: wine.bars.tannin, acidity: wine.bars.acidity, body: wine.bars.body }} palette={wine.color} compact />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'baseline', gap: 10 }}>
          <span style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 11, color: INK_SOFT }}>cellar price</span>
          <span style={{ fontFamily: serifDisp, fontWeight: 500, fontSize: 22, color: INK }}>${wine.price}</span>
        </div>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// A · Detail spread for ONE wine
function VinDetail({ w, h, wine }) {
  const accent = wine.color.accent;
  return (
    <PaperFrame w={w} h={h} no="III" tint={wine.color.tint} label={`Folio · The Estate`}>
      <Masthead small dateline={`The Estate · ${wine.region}, ${wine.country}`} />
      {/* hero */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: 24, padding: '26px 40px 14px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          <Bottle palette={wine.color} shape={wine.region === 'Burgundy' ? 'burgundy' : 'bordeaux'} size={68} />
          <div style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 11, color: INK_SOFT, textAlign: 'center', letterSpacing: 1 }}>
            in the glass — {wine.color.glass.toUpperCase()}
          </div>
          <GlassPour palette={wine.color} size={86} fill={0.5} />
        </div>
        <div>
          <div style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 11, letterSpacing: 4, textTransform: 'uppercase', color: accent }}>
            Review № {wine.rank.toString().padStart(2, '0')} · {wine.appellation}
          </div>
          <div style={{ fontFamily: serifDisp, fontWeight: 400, fontSize: 64, lineHeight: 0.92, color: INK, letterSpacing: -1.5, marginTop: 6 }}>
            {wine.name}
          </div>
          <div style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 22, color: INK_SOFT, marginTop: 4 }}>
            {wine.producer} · {wine.vintage}
          </div>
          <div style={{ marginTop: 14, fontFamily: serifBody, fontSize: 14, lineHeight: 1.55, color: INK, columnCount: 2, columnGap: 18, columnRule: `0.5px solid ${INK}` }}>
            <span style={{ fontFamily: serifDisp, fontWeight: 500, fontSize: 56, float: 'left', lineHeight: 0.85, marginRight: 6, marginTop: 4, color: accent }}>
              {wine.palate[0]}
            </span>
            {wine.palate.slice(1)}
          </div>
        </div>
      </div>
      <div style={{ padding: '0 40px' }}><RuleDouble color={INK} opacity={0.5} /></div>

      {/* lower triptych: aroma wheel · structure · terroir */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1px 1fr 1px 1fr', gap: 0, padding: '20px 40px 24px' }}>
        <Panel title="In the Nose" caption="aroma compass">
          <FlavorWheel data={wine.wheel} palette={wine.color} size={210} />
        </Panel>
        <div style={{ background: INK, opacity: 0.18 }} />
        <Panel title="On the Palate" caption="structure">
          <div style={{ paddingTop: 10 }}>
            <StructureBars bars={wine.bars} palette={wine.color} />
          </div>
          <div style={{ marginTop: 14, fontFamily: serifBody, fontStyle: 'italic', fontSize: 12, color: INK_SOFT, textAlign: 'center' }}>
            {wine.nose}
          </div>
        </Panel>
        <div style={{ background: INK, opacity: 0.18 }} />
        <Panel title="Terroir" caption={`${wine.region}, ${wine.country}`}>
          <RegionMap country={wine.country} lat={wine.coords.lat} lon={wine.coords.lon} label={wine.appellation.split(' ·')[0]} palette={wine.color} size={150} />
          <div style={{ marginTop: 8, fontFamily: serifDisp, fontSize: 11, letterSpacing: 2, textTransform: 'uppercase', color: INK_SOFT, textAlign: 'center' }}>
            {wine.grape}
          </div>
        </Panel>
      </div>

      {/* footer — pairing + drinking window + price */}
      <div style={{ position: 'absolute', left: 40, right: 40, bottom: 56 }}>
        <RuleDouble color={INK} opacity={0.45} />
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr 0.8fr', gap: 24, marginTop: 16 }}>
          <div>
            <div style={{ fontFamily: serifDisp, fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 6 }}>Pairing</div>
            <div style={{ fontFamily: serifBody, fontStyle: 'italic', fontSize: 14, color: INK, lineHeight: 1.5 }}>
              {wine.pairs.join(' · ')}
            </div>
          </div>
          <div>
            <div style={{ fontFamily: serifDisp, fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 6 }}>Drinking Window</div>
            <DrinkingWindow drink={wine.drink} palette={wine.color} />
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: serifDisp, fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 6 }}>The Editor</div>
            <div style={{ fontFamily: serifDisp, fontWeight: 500, fontSize: 56, color: accent, lineHeight: 0.9 }}>{wine.critic.score}</div>
            <div style={{ fontFamily: serifBody, fontStyle: 'italic', fontSize: 12, color: INK_SOFT }}>${wine.price} · {wine.abv}% abv</div>
          </div>
        </div>
      </div>
    </PaperFrame>
  );
}

function Panel({ title, caption, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '0 14px' }}>
      <div style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 11, letterSpacing: 3, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 2 }}>{caption}</div>
      <div style={{ fontFamily: serifDisp, fontSize: 22, color: INK, marginBottom: 14 }}>{title}</div>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
        {children}
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// A · Compare — two reviews side by side
function VinCompare({ w, h, wines }) {
  const [a, b] = wines;
  return (
    <PaperFrame w={w} h={h} no="IV" label="Folio · Side by Side">
      <Masthead small dateline="A comparative tasting · two bottles, one table" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1px 1fr', height: 'calc(100% - 130px)' }}>
        {[a, b].map((wine, i) => (
          <React.Fragment key={wine.id}>
            {i === 1 && <div style={{ background: INK, opacity: 0.4 }} />}
            <div style={{ padding: '22px 28px', display: 'flex', flexDirection: 'column', gap: 14, position: 'relative' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <div>
                  <div style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 10, letterSpacing: 3, textTransform: 'uppercase', color: wine.color.accent }}>
                    {i === 0 ? 'À gauche' : 'À droite'} · {wine.appellation}
                  </div>
                  <div style={{ fontFamily: serifDisp, fontSize: 32, lineHeight: 1, color: INK, marginTop: 2, letterSpacing: -0.5 }}>
                    {wine.name}
                  </div>
                  <div style={{ fontFamily: serifBody, fontStyle: 'italic', fontSize: 13, color: INK_SOFT, marginTop: 2 }}>
                    {wine.producer} · {wine.vintage}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <Bottle palette={wine.color} shape={wine.region === 'Burgundy' ? 'burgundy' : 'bordeaux'} size={36} />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 4 }}>
                <FlavorWheel data={wine.wheel} palette={wine.color} size={170} />
              </div>

              <StructureBars bars={wine.bars} palette={wine.color} />

              <div style={{ fontFamily: serifBody, fontSize: 12.5, lineHeight: 1.55, color: INK }}>
                <span style={{ fontFamily: serifDisp, fontStyle: 'italic', color: wine.color.accent }}>"</span>
                {wine.palate.split('. ')[0]}.{' '}
                <span style={{ fontFamily: serifDisp, fontStyle: 'italic', color: wine.color.accent }}>"</span>
              </div>

              <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontFamily: serifDisp, fontWeight: 500, fontSize: 32, color: wine.color.accent }}>
                  {wine.critic.score}
                  <span style={{ fontSize: 12, color: INK_SOFT, opacity: 0.7 }}> · ${wine.price}</span>
                </span>
                <span style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 12, color: INK_SOFT }}>peak {wine.drink.peak}</span>
              </div>
            </div>
          </React.Fragment>
        ))}
      </div>

      {/* verdict band */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, padding: '14px 40px 44px', background: INK, color: PAPER }}>
        <div style={{ fontFamily: serifDisp, fontStyle: 'italic', fontSize: 9, letterSpacing: 4, textTransform: 'uppercase', opacity: 0.7 }}>The Editor's Verdict</div>
        <div style={{ fontFamily: serifDisp, fontSize: 18, lineHeight: 1.35, marginTop: 4, fontStyle: 'italic' }}>
          "Open the <span style={{ color: a.color.tint }}>{a.name.split(' ').slice(0, 2).join(' ')}</span> first — it is generous tonight; pour the <span style={{ color: b.color.tint }}>{b.name.split(' ').slice(0, 2).join(' ')}</span> with the second course, decanted ninety minutes."
        </div>
      </div>
    </PaperFrame>
  );
}

Object.assign(window, { VinPreferences, VinList, VinDetail, VinCompare });
