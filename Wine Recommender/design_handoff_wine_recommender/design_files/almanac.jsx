// Variation B — "The Cellar Almanac"
// A bound sommelier's atlas/journal. Lined parchment, annotated diagrams,
// IM Fell-feel display + serif body. Asymmetric: spine on left, marginalia
// in margin, content unfolds like a journal entry.

const PARCH = '#ece0c2';
const PARCH_DEEP = '#dccda4';
const ALMINK = '#231408';
const ALMINK_SOFT = '#52371f';
const ALMRULE = 'rgba(35,20,8,0.4)';
const ALMRED = '#6e1a1c';

const dispFam = "'IM Fell English', 'Cormorant Garamond', serif";
const bodyFam = "'EB Garamond', 'IM Fell English', serif";
const handFam = "'IM Fell English', 'EB Garamond', serif"; // italicized for "handwriting"

// ─── Bound journal page with stitched binding on the left
function JournalPage({ children, w, h, signature, leftTab }) {
  return (
    <div style={{
      width: w, height: h, position: 'relative',
      background: `
        radial-gradient(120% 80% at 30% 0%, rgba(255,240,200,0.45), transparent 60%),
        radial-gradient(80% 60% at 100% 100%, rgba(80,40,10,0.15), transparent 60%),
        ${PARCH}
      `,
      color: ALMINK, fontFamily: bodyFam, overflow: 'hidden',
      boxShadow: 'inset 24px 0 30px -20px rgba(60,30,5,0.35), inset -20px -20px 50px rgba(60,30,5,0.08)',
    }}>
      {/* lined paper rules (every 26px) */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        backgroundImage: `repeating-linear-gradient(to bottom, transparent 0, transparent 25px, rgba(35,20,8,0.07) 25px, rgba(35,20,8,0.07) 26px)`,
      }} />
      {/* binding edge */}
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 38, background: 'linear-gradient(to right, rgba(60,30,5,0.18), transparent)' }} />
      <div style={{ position: 'absolute', left: 38, top: 0, bottom: 0, width: 1, background: ALMRED, opacity: 0.4 }} />
      <div style={{ position: 'absolute', left: 42, top: 0, bottom: 0, width: 0.5, background: ALMRED, opacity: 0.25 }} />
      {/* stitch marks */}
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} style={{
          position: 'absolute', left: 18, top: 30 + i * (h - 60) / 11,
          width: 8, height: 1.5, background: ALMINK_SOFT, opacity: 0.5, transform: 'rotate(-12deg)',
        }} />
      ))}
      {leftTab && (
        <div style={{
          position: 'absolute', left: -2, top: 80, transform: 'rotate(-90deg)', transformOrigin: 'top left',
          fontFamily: dispFam, fontSize: 11, letterSpacing: 6, textTransform: 'uppercase', color: ALMINK_SOFT,
        }}>{leftTab}</div>
      )}
      {/* noise */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none', opacity: 0.5,
        backgroundImage: 'radial-gradient(rgba(80,40,10,0.05) 1px, transparent 1px)',
        backgroundSize: '4px 4px', mixBlendMode: 'multiply',
      }} />
      {children}
      {signature && (
        <div style={{
          position: 'absolute', right: 22, bottom: 14,
          fontFamily: handFam, fontStyle: 'italic', fontSize: 12, color: ALMRED, opacity: 0.7,
          transform: 'rotate(-2deg)',
        }}>— {signature}</div>
      )}
    </div>
  );
}

// Header style — small, like a journal header with date stamps
function JournalHeader({ title, sub, idx, total, chapter }) {
  return (
    <div style={{ padding: '20px 40px 12px 80px', display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', borderBottom: `1px solid ${ALMINK}`, borderBottomStyle: 'double' }}>
      <div>
        <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 4, textTransform: 'uppercase', color: ALMINK_SOFT }}>
          Chapter {chapter || 'I'} · The Cellar Almanac
        </div>
        <div style={{ fontFamily: dispFam, fontSize: 32, lineHeight: 1, color: ALMINK, letterSpacing: -0.2, marginTop: 2 }}>{title}</div>
        {sub && <div style={{ fontFamily: bodyFam, fontStyle: 'italic', fontSize: 13, color: ALMINK_SOFT, marginTop: 3 }}>{sub}</div>}
      </div>
      <div style={{ textAlign: 'right' }}>
        <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 11, color: ALMINK_SOFT }}>13 May, the year MMXXVI</div>
        {idx && <div style={{ fontFamily: dispFam, fontSize: 11, letterSpacing: 3, color: ALMINK_SOFT, marginTop: 4 }}>Folio {idx} / {total}</div>}
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────
// B · Preferences — sommelier intake sheet, handwritten feel
function AlmPreferences({ w, h }) {
  return (
    <JournalPage w={w} h={h} signature="recorded by the sommelier" leftTab="Folio I · Intake">
      <JournalHeader title="An Evening's Intake" sub="Particulars logged for the wine selection" chapter="I" idx="01" total="04" />
      <div style={{ padding: '26px 56px 24px 80px', display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 36 }}>
        <div>
          <Stamp label="On this date" value="Wednesday · 13 May, 2026" />
          <Stamp label="In attendance" value="four guests" />
          <Stamp label="Manner of meal" value="Charred ribeye, porcini-Roquefort, dark chocolate" />
          <Stamp label="Cellar tendencies" value="Sangiovese · Nebbiolo · old-world reds" />
          <Stamp label="Wines previously praised" value="Brunello (2010, 2015) · Bandol · cool-vintage Burgundy" />
          <div style={{ marginTop: 16 }}>
            <Annotated label="Sommelier's note" body="Steer toward structured, savoury reds; one curiosity permitted. Avoid heavy new oak — the guest of honour rates it poorly." />
          </div>
        </div>

        <div style={{ position: 'relative' }}>
          <div style={{ fontFamily: dispFam, fontSize: 11, letterSpacing: 4, textTransform: 'uppercase', color: ALMINK_SOFT, marginBottom: 8 }}>
            Preferences · the dial
          </div>
          {/* dials */}
          <div style={{ display: 'grid', gap: 16 }}>
            <Dial label="Safer ◀ Adventurous ▶" value={6.5} palette={{ ink: ALMINK, accent: ALMRED }} />
            <Dial label="Light ◀ Bold ▶" value={7} palette={{ ink: ALMINK, accent: ALMRED }} />
            <Dial label="Young ◀ Aged ▶" value={6} palette={{ ink: ALMINK, accent: ALMRED }} />
            <Dial label="Food-first ◀ Wine-first ▶" value={4} palette={{ ink: ALMINK, accent: ALMRED }} />
          </div>
          <div style={{ marginTop: 24, padding: '14px 16px', border: `1px solid ${ALMINK}`, borderStyle: 'dashed', background: 'rgba(255,250,235,0.4)' }}>
            <div style={{ fontFamily: dispFam, fontSize: 10, letterSpacing: 3, textTransform: 'uppercase', color: ALMINK_SOFT, marginBottom: 4 }}>Ceiling per bottle</div>
            <div style={{ fontFamily: dispFam, fontSize: 36, lineHeight: 1, color: ALMRED, letterSpacing: -0.5 }}>$200</div>
            <div style={{ fontFamily: bodyFam, fontStyle: 'italic', fontSize: 12, color: ALMINK_SOFT, marginTop: 2 }}>three bottles, one to keep</div>
          </div>

          <button style={{
            marginTop: 22, width: '100%',
            fontFamily: dispFam, fontSize: 14, letterSpacing: 4, textTransform: 'uppercase',
            padding: '14px 18px', background: ALMINK, color: PARCH, border: 'none', cursor: 'pointer',
          }}>
            Consult the almanac →
          </button>
        </div>
      </div>

      {/* footer — marginalia */}
      <div style={{ position: 'absolute', left: 80, right: 40, bottom: 32, display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <div style={{ fontFamily: handFam, fontStyle: 'italic', fontSize: 13, color: ALMRED, transform: 'rotate(-1deg)', opacity: 0.85 }}>
          ✱ 412 bottles on file · 28 producers represented
        </div>
        <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 11, color: ALMINK_SOFT, letterSpacing: 2 }}>→ next: the recommendations</div>
      </div>
    </JournalPage>
  );
}

function Stamp({ label, value }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ fontFamily: dispFam, fontSize: 10, letterSpacing: 4, textTransform: 'uppercase', color: ALMINK_SOFT, marginBottom: 2 }}>{label}</div>
      <div style={{ fontFamily: handFam, fontStyle: 'italic', fontSize: 18, color: ALMINK, borderBottom: `1px dotted ${ALMINK}`, paddingBottom: 4 }}>{value}</div>
    </div>
  );
}

function Annotated({ label, body }) {
  return (
    <div style={{ position: 'relative', padding: '10px 14px', borderLeft: `2px solid ${ALMRED}`, background: 'rgba(110,26,28,0.04)' }}>
      <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 3, textTransform: 'uppercase', color: ALMRED, marginBottom: 4 }}>{label}</div>
      <div style={{ fontFamily: bodyFam, fontStyle: 'italic', fontSize: 13, lineHeight: 1.5, color: ALMINK }}>{body}</div>
    </div>
  );
}

function Dial({ label, value, palette }) {
  return (
    <div>
      <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 11, letterSpacing: 1, color: palette.ink, opacity: 0.8, marginBottom: 4 }}>{label}</div>
      <svg viewBox="0 0 240 16" preserveAspectRatio="none" width="100%" height={14}>
        <line x1={0} y1={8} x2={240} y2={8} stroke={palette.ink} strokeOpacity={0.4} strokeWidth={0.6} />
        {Array.from({ length: 21 }).map((_, i) => (
          <line key={i} x1={i * 12} y1={i % 5 === 0 ? 2 : 4} x2={i * 12} y2={i % 5 === 0 ? 14 : 12} stroke={palette.ink} strokeOpacity={0.5} strokeWidth={0.6} />
        ))}
        <polygon points={`${value * 24},0 ${value * 24 + 6},8 ${value * 24},14 ${value * 24 - 6},8`} fill={palette.accent} />
      </svg>
    </div>
  );
}

// ───────────────────────────────────────────────────────────
// B · Recommendations — almanac entries with marginalia
function AlmList({ w, h, wines }) {
  return (
    <JournalPage w={w} h={h} signature="composed for the evening" leftTab="Folio II · The Flight">
      <JournalHeader title="Three Bottles" sub="A flight drawn from the cellar and houses we trust" chapter="II" idx="02" total="04" />

      {/* a chart at top */}
      <div style={{ padding: '18px 40px 0 80px', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 12, color: ALMINK_SOFT, letterSpacing: 2, textTransform: 'uppercase' }}>
          Sorted by fit · ★ structure  ✦ adventure
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          {['under $80', 'food first', 'more adventurous', 'cellar safer'].map((t, i) => (
            <span key={t} style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 11, color: ALMINK, padding: '2px 8px', border: `0.5px dashed ${ALMINK}`, opacity: 0.7 }}>{t}</span>
          ))}
        </div>
      </div>

      <div style={{ padding: '18px 40px 20px 80px', display: 'grid', gap: 16 }}>
        {wines.map((wine) => <AlmanacEntry key={wine.id} wine={wine} />)}
      </div>

      <div style={{ position: 'absolute', left: 80, right: 40, bottom: 32, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontFamily: handFam, fontStyle: 'italic', fontSize: 13, color: ALMRED, transform: 'rotate(-0.6deg)' }}>
          ☞ Open in order. Decant the second.
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button style={almBtnGhost}>↻ recompose</button>
          <button style={almBtnPrimary}>side by side ⇆</button>
        </div>
      </div>
    </JournalPage>
  );
}

const almBtnGhost = {
  fontFamily: dispFam, fontSize: 11, letterSpacing: 3, textTransform: 'uppercase',
  padding: '8px 14px', background: 'transparent', color: ALMINK, border: `1px solid ${ALMINK}`, cursor: 'pointer',
};
const almBtnPrimary = {
  fontFamily: dispFam, fontSize: 11, letterSpacing: 3, textTransform: 'uppercase',
  padding: '8px 14px', background: ALMINK, color: PARCH, border: `1px solid ${ALMINK}`, cursor: 'pointer',
};

function AlmanacEntry({ wine }) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '38px 78px 1fr 160px 130px', gap: 14, alignItems: 'stretch',
      padding: '10px 0', borderBottom: `0.5px dashed ${ALMINK}`,
    }}>
      {/* rank */}
      <div style={{ position: 'relative' }}>
        <div style={{
          position: 'absolute', top: 4, left: 0, width: 30, height: 30,
          border: `1.5px solid ${ALMRED}`, borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: dispFam, fontWeight: 600, fontSize: 16, color: ALMRED,
        }}>{wine.rank}</div>
        <div style={{ position: 'absolute', top: 36, left: 14, bottom: 4, width: 1, borderLeft: `1px dotted ${ALMINK}` }} />
      </div>

      {/* mini map */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <RegionMap country={wine.country} lat={wine.coords.lat} lon={wine.coords.lon} palette={wine.color} size={78} />
        <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 9, letterSpacing: 1, color: ALMINK_SOFT, marginTop: -8 }}>
          {wine.region}
        </div>
      </div>

      {/* main */}
      <div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
          <div style={{ fontFamily: dispFam, fontWeight: 500, fontSize: 22, color: ALMINK, letterSpacing: -0.2, lineHeight: 1.1 }}>{wine.name}</div>
          <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 14, color: ALMINK_SOFT }}>· {wine.vintage}</div>
        </div>
        <div style={{ fontFamily: bodyFam, fontStyle: 'italic', fontSize: 12, color: ALMINK_SOFT }}>{wine.producer} · {wine.grape}</div>
        <div style={{ fontFamily: bodyFam, fontSize: 12.5, lineHeight: 1.5, color: ALMINK, marginTop: 6, maxWidth: '95%' }}>
          {wine.palate.split('. ')[0]}.
        </div>
        <div style={{ display: 'flex', gap: 10, marginTop: 6, flexWrap: 'wrap' }}>
          {wine.fits.slice(0, 4).map((f, i) => (
            <span key={i} style={{ fontFamily: handFam, fontStyle: 'italic', fontSize: 11, color: ALMRED }}>
              <span style={{ marginRight: 3, opacity: 0.6 }}>✦</span>{f}
            </span>
          ))}
        </div>
      </div>

      {/* structure bars */}
      <div style={{ alignSelf: 'center' }}>
        <StructureBars bars={{ tannin: wine.bars.tannin, acidity: wine.bars.acidity, body: wine.bars.body }} palette={wine.color} compact />
      </div>

      {/* price/score */}
      <div style={{ borderLeft: `0.5px dotted ${ALMINK}`, paddingLeft: 14, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontFamily: dispFam, fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: ALMINK_SOFT }}>Marked at</div>
          <div style={{ fontFamily: dispFam, fontSize: 24, color: ALMINK, lineHeight: 1 }}>${wine.price}</div>
        </div>
        <div>
          <div style={{ fontFamily: dispFam, fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: ALMINK_SOFT }}>Score</div>
          <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 18, color: ALMRED }}>{wine.critic.score}<span style={{ fontSize: 10, color: ALMINK_SOFT, marginLeft: 2 }}>{wine.critic.source}</span></div>
        </div>
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────
// B · Detail — almanac entry, full page, with diagram + marginalia
function AlmDetail({ w, h, wine }) {
  return (
    <JournalPage w={w} h={h} signature={`tasted by candlelight, ${wine.vintage}`} leftTab={`Folio III · ${wine.region}`}>
      <JournalHeader title={wine.name} sub={`${wine.producer} · ${wine.appellation} · ${wine.vintage}`} chapter="III" idx="03" total="04" />

      <div style={{ padding: '20px 40px 0 80px', display: 'grid', gridTemplateColumns: '1fr 280px', gap: 30 }}>
        {/* left: tasting note */}
        <div>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
            <Bottle palette={wine.color} shape={wine.region === 'Burgundy' ? 'burgundy' : 'bordeaux'} size={48} />
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 4, textTransform: 'uppercase', color: ALMRED, marginBottom: 4 }}>
                Tasting record
              </div>
              <div style={{ fontFamily: bodyFam, fontSize: 14, lineHeight: 1.6, color: ALMINK }}>
                <span style={{ fontFamily: dispFam, fontWeight: 500, fontSize: 38, float: 'left', lineHeight: 0.85, marginRight: 6, marginTop: 4, color: ALMRED }}>
                  {wine.palate[0]}
                </span>
                {wine.palate.slice(1)}
              </div>
            </div>
          </div>

          {/* nose */}
          <div style={{ marginTop: 18 }}>
            <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 11, letterSpacing: 3, textTransform: 'uppercase', color: ALMINK_SOFT, marginBottom: 6 }}>
              In the nose · the aroma compass
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, alignItems: 'center' }}>
              <FlavorWheel data={wine.wheel} palette={wine.color} size={200} />
              <div>
                <Stamp label="Dominant" value={Object.entries(wine.wheel).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([k])=>k).join(' · ').toLowerCase()} />
                <Stamp label="Background" value={Object.entries(wine.wheel).sort((a,b)=>b[1]-a[1]).slice(3,6).map(([k])=>k).join(' · ').toLowerCase()} />
              </div>
            </div>
          </div>

          {/* structure */}
          <div style={{ marginTop: 6 }}>
            <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 11, letterSpacing: 3, textTransform: 'uppercase', color: ALMINK_SOFT, marginBottom: 6 }}>
              On the palate · the structure
            </div>
            <StructureBars bars={wine.bars} palette={wine.color} />
          </div>
        </div>

        {/* right column: terroir + glass + window */}
        <div style={{ paddingLeft: 16, borderLeft: `0.5px dashed ${ALMINK}` }}>
          <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 11, letterSpacing: 3, textTransform: 'uppercase', color: ALMINK_SOFT, marginBottom: 6 }}>
            The terroir
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', position: 'relative' }}>
            <RegionMap country={wine.country} lat={wine.coords.lat} lon={wine.coords.lon} label={wine.appellation.split(' ·')[0]} palette={wine.color} size={200} />
          </div>
          <div style={{ fontFamily: handFam, fontStyle: 'italic', fontSize: 12, color: ALMRED, textAlign: 'center', marginTop: -10, transform: 'rotate(-1deg)' }}>
            ☞ {wine.appellation}
          </div>

          {/* glass color */}
          <div style={{ marginTop: 18, display: 'flex', alignItems: 'center', gap: 14 }}>
            <GlassPour palette={wine.color} size={70} fill={0.55} />
            <div>
              <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 3, textTransform: 'uppercase', color: ALMINK_SOFT }}>In the glass</div>
              <div style={{ fontFamily: handFam, fontStyle: 'italic', fontSize: 16, color: ALMINK, lineHeight: 1.2 }}>
                {colorWord(wine.color.glass)}
              </div>
              <div style={{ width: 60, height: 16, background: wine.color.glass, marginTop: 4, border: `0.5px solid ${ALMINK}` }} />
            </div>
          </div>

          <div style={{ marginTop: 18 }}>
            <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 3, textTransform: 'uppercase', color: ALMINK_SOFT, marginBottom: 6 }}>Drinking window</div>
            <DrinkingWindow drink={wine.drink} palette={wine.color} />
          </div>

          <div style={{ marginTop: 18, padding: '10px 12px', borderTop: `1px solid ${ALMINK}`, borderBottom: `1px solid ${ALMINK}`, borderTopStyle: 'double' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 3, color: ALMINK_SOFT, textTransform: 'uppercase' }}>Marked</div>
                <div style={{ fontFamily: dispFam, fontSize: 22, color: ALMINK }}>${wine.price}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 3, color: ALMINK_SOFT, textTransform: 'uppercase' }}>Score</div>
                <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 22, color: ALMRED }}>{wine.critic.score}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ position: 'absolute', left: 80, right: 40, bottom: 26 }}>
        <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 3, textTransform: 'uppercase', color: ALMINK_SOFT, marginBottom: 4 }}>
          To pair · the table tonight
        </div>
        <div style={{ fontFamily: handFam, fontStyle: 'italic', fontSize: 15, color: ALMRED, transform: 'rotate(-0.4deg)' }}>
          {wine.pairs.join(' · ')}
        </div>
      </div>
    </JournalPage>
  );
}

function colorWord(hex) {
  const named = {
    '#7d1f24': 'deep brick · garnet rim',
    '#8a2a2e': 'garnet · brick rim',
    '#d9b743': 'pale straw · greenish glints',
  };
  return named[hex] || 'deep ruby';
}

// ───────────────────────────────────────────────────────────
// B · Compare — side-by-side journal entries with central comparator
function AlmCompare({ w, h, wines }) {
  const [a, b] = wines;
  // build comparison rows
  const rows = [
    { k: 'tannin', label: 'Tannin' },
    { k: 'acidity', label: 'Acidity' },
    { k: 'body', label: 'Body' },
    { k: 'oak', label: 'Oak' },
  ];
  return (
    <JournalPage w={w} h={h} signature="comparative tasting" leftTab="Folio IV · Side by Side">
      <JournalHeader title="Side by Side" sub="The two foremost selections, weighed against one another" chapter="IV" idx="04" total="04" />

      {/* heads */}
      <div style={{ padding: '18px 30px 0 80px', display: 'grid', gridTemplateColumns: '1fr 130px 1fr', gap: 14, alignItems: 'start' }}>
        <WineHead wine={a} side="left" />
        <div style={{ textAlign: 'center', paddingTop: 22 }}>
          <Fleuron color={ALMINK} size={20} />
          <div style={{ fontFamily: handFam, fontStyle: 'italic', fontSize: 14, color: ALMRED, marginTop: 6, transform: 'rotate(-2deg)' }}>vs.</div>
        </div>
        <WineHead wine={b} side="right" />
      </div>

      {/* aroma compasses overlaid would be too messy; show both */}
      <div style={{ padding: '8px 30px 0 80px', display: 'grid', gridTemplateColumns: '1fr 130px 1fr', gap: 14 }}>
        <div style={{ display: 'flex', justifyContent: 'center' }}><FlavorWheel data={a.wheel} palette={a.color} size={160} /></div>
        <div style={{ textAlign: 'center', alignSelf: 'center' }}>
          <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 3, color: ALMINK_SOFT, textTransform: 'uppercase' }}>aroma compass</div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'center' }}><FlavorWheel data={b.wheel} palette={b.color} size={160} /></div>
      </div>

      {/* structure comparator */}
      <div style={{ padding: '12px 80px 8px', marginTop: 4 }}>
        <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 11, letterSpacing: 3, color: ALMINK_SOFT, textTransform: 'uppercase', marginBottom: 8, textAlign: 'center' }}>
          structure · weighed
        </div>
        <div style={{ display: 'grid', gap: 6 }}>
          {rows.map(({ k, label }) => (
            <DoubleBar key={k} label={label} aWine={a} bWine={b} value={k} />
          ))}
        </div>
      </div>

      <div style={{ position: 'absolute', left: 80, right: 40, bottom: 28, padding: '12px 0 0', borderTop: `1px solid ${ALMINK}`, borderTopStyle: 'double' }}>
        <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 3, color: ALMINK_SOFT, textTransform: 'uppercase', marginBottom: 4 }}>
          The sommelier's verdict
        </div>
        <div style={{ fontFamily: handFam, fontStyle: 'italic', fontSize: 15, color: ALMRED, lineHeight: 1.5, transform: 'rotate(-0.4deg)' }}>
          ☞ Open the <strong style={{ color: a.color.accent }}>{a.name.split(' ')[0]}</strong> first — it is generous tonight.<br />
          Pour the <strong style={{ color: b.color.accent }}>{b.name.split(' ')[0]}</strong> with the second course, decanted ninety minutes.
        </div>
      </div>
    </JournalPage>
  );
}

function WineHead({ wine, side }) {
  return (
    <div style={{ textAlign: side === 'right' ? 'right' : 'left' }}>
      <div style={{ fontFamily: dispFam, fontStyle: 'italic', fontSize: 10, letterSpacing: 4, textTransform: 'uppercase', color: wine.color.accent }}>
        {wine.appellation}
      </div>
      <div style={{ fontFamily: dispFam, fontWeight: 500, fontSize: 22, color: ALMINK, lineHeight: 1.05, marginTop: 2 }}>{wine.name}</div>
      <div style={{ fontFamily: bodyFam, fontStyle: 'italic', fontSize: 12, color: ALMINK_SOFT }}>{wine.producer} · {wine.vintage}</div>
      <div style={{ marginTop: 4, display: 'flex', gap: 10, justifyContent: side === 'right' ? 'flex-end' : 'flex-start', fontFamily: dispFam, fontSize: 13, color: ALMINK }}>
        <span style={{ fontStyle: 'italic', color: wine.color.accent }}>{wine.critic.score}</span>
        <span>·</span>
        <span>${wine.price}</span>
      </div>
    </div>
  );
}

function DoubleBar({ label, aWine, bWine, value }) {
  const av = aWine.bars[value] || 0;
  const bv = bWine.bars[value] || 0;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 80px 1fr', alignItems: 'center', gap: 8 }}>
      <svg viewBox="0 0 200 10" preserveAspectRatio="none" width="100%" height={10} style={{ transform: 'scaleX(-1)' }}>
        <line x1={0} y1={5} x2={200} y2={5} stroke={ALMINK} strokeOpacity={0.2} strokeWidth={0.5} />
        <rect x={200 - av * 20} y={3} width={av * 20} height={4} fill={aWine.color.accent} />
      </svg>
      <div style={{ textAlign: 'center', fontFamily: dispFam, fontStyle: 'italic', fontSize: 12, color: ALMINK }}>
        <span style={{ color: aWine.color.accent, marginRight: 4 }}>{av}</span>
        {label}
        <span style={{ color: bWine.color.accent, marginLeft: 4 }}>{bv}</span>
      </div>
      <svg viewBox="0 0 200 10" preserveAspectRatio="none" width="100%" height={10}>
        <line x1={0} y1={5} x2={200} y2={5} stroke={ALMINK} strokeOpacity={0.2} strokeWidth={0.5} />
        <rect x={0} y={3} width={bv * 20} height={4} fill={bWine.color.accent} />
      </svg>
    </div>
  );
}

Object.assign(window, { AlmPreferences, AlmList, AlmDetail, AlmCompare });
