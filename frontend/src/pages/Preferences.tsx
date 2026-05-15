import { useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import Fleuron from '@/design/atoms/Fleuron';
import RuleDouble from '@/design/atoms/RuleDouble';
import Field from '@/design/Field';
import { INK, INK_SOFT, OXBLOOD, PAPER } from '@/design/tokens';
import { recommendRecommendPost } from '@/client';
import type { RecommendationResponse } from '@/client/types.gen';

type SourceMode = 'cellar' | 'winelist';

const FOLIO = [
  ['I.', 'The Intake', 'Particulars of the evening'],
  ['II.', 'Three Reviews', 'Composed for the night'],
  ['III.', 'The Estate', 'Profile of a bottle'],
  ['IV.', 'Side by Side', 'A comparative tasting'],
] as const;

export default function Preferences() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [sourceMode, setSourceMode] = useState<SourceMode>('cellar');
  const [wineListFile, setWineListFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const [occasion, setOccasion] = useState('');
  const [menu, setMenu] = useState('');
  const [cellarLeans, setCellarLeans] = useState('');
  const [temperament, setTemperament] = useState('');
  const [ceiling, setCeiling] = useState('');
  const [bottles, setBottles] = useState('');

  const [testFixture, setTestFixture] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const dateline = new Date().toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' });

  const handleFile = (file: File | null) => {
    setWineListFile(file);
    setError('');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0] ?? null;
    handleFile(file);
  };

  const handleSubmit = async () => {
    const meal = [occasion, menu].filter(Boolean).join(' — ');
    if (!meal.trim()) {
      setError('Please describe the occasion or menu.');
      return;
    }
    if (sourceMode === 'winelist' && !wineListFile) {
      setError('Please upload a wine list.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const listFile = wineListFile ?? new File(['cellar'], 'cellar.txt', { type: 'text/plain' });
      const styleTerms = [cellarLeans, temperament].filter(Boolean).join('; ') || undefined;

      const response = await recommendRecommendPost({
        body: {
          wine_list: listFile,
          meal,
          style_terms: styleTerms,
          test_fixture: testFixture || undefined,
        },
      });

      if (response.data) {
        navigate('/flight', { state: { recommendations: response.data as RecommendationResponse } });
      } else {
        setError('No recommendations returned.');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Something went wrong.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PaperFrame>
      <Masthead dateline={`Issue prepared for one guest · ${dateline}`} />

      <div
        style={{
          padding: '12px 44px 0',
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        <Link
          to="/history"
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
            marginRight: 20,
          }}
        >
          Past flights
        </Link>
        <Link
          to="/profile"
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
          Your palate
        </Link>
      </div>

      <div
        style={{
          padding: '24px 44px 200px',
          display: 'grid',
          gridTemplateColumns: '1fr 1.4fr',
          gap: 36,
        }}
      >
        {/* Left column — editorial prompt */}
        <div>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: 14,
              color: INK_SOFT,
              marginBottom: 6,
            }}
          >
            The Editor inquires:
          </div>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontSize: 44,
              lineHeight: 0.96,
              letterSpacing: -1,
              color: INK,
            }}
          >
            What will <span style={{ fontStyle: 'italic' }}>you</span> open
            <br />
            tonight?
          </div>
          <div
            style={{
              marginTop: 14,
              fontFamily: "'EB Garamond', serif",
              fontSize: 13,
              lineHeight: 1.55,
              color: INK_SOFT,
              fontStyle: 'italic',
            }}
          >
            Provide a few particulars — the meal, the company, the temperament of the
            evening — and our cellar editor will compose a flight from your collection
            and the houses we admire.
          </div>
          <div style={{ marginTop: 22 }}>
            <Fleuron color={INK} size={20} />
          </div>
        </div>

        {/* Right column — form */}
        <div style={{ display: 'grid', gap: 18 }}>
          {/* Source mode pill toggle */}
          <div>
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 9,
                letterSpacing: 3,
                textTransform: 'uppercase',
                color: INK_SOFT,
                opacity: 0.85,
                marginBottom: 8,
              }}
            >
              Source
            </div>
            <div style={{ display: 'flex', border: `1px solid ${INK}`, width: 'fit-content' }}>
              {(['cellar', 'winelist'] as SourceMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setSourceMode(mode)}
                  style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 11,
                    letterSpacing: 2,
                    textTransform: 'uppercase',
                    padding: '6px 16px',
                    background: sourceMode === mode ? INK : 'transparent',
                    color: sourceMode === mode ? PAPER : INK,
                    border: 'none',
                    cursor: 'pointer',
                  }}
                >
                  {mode === 'cellar' ? 'From my cellar' : 'From a wine list'}
                </button>
              ))}
            </div>
          </div>

          {/* Wine list drop zone */}
          {sourceMode === 'winelist' && (
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `1px solid ${isDragging ? INK : 'rgba(31,18,10,0.3)'}`,
                padding: '20px',
                textAlign: 'center',
                cursor: 'pointer',
                background: isDragging ? 'rgba(31,18,10,0.03)' : 'transparent',
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                style={{ display: 'none' }}
                onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
              />
              {wineListFile ? (
                <div>
                  <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 14, color: INK }}>
                    {wineListFile.name}
                  </div>
                  <div
                    style={{
                      fontFamily: "'EB Garamond', serif",
                      fontStyle: 'italic',
                      fontSize: 11,
                      color: INK_SOFT,
                      marginTop: 4,
                    }}
                  >
                    Click to change
                  </div>
                </div>
              ) : (
                <div>
                  <div
                    style={{
                      fontFamily: "'Cormorant Garamond', serif",
                      fontStyle: 'italic',
                      fontSize: 11,
                      letterSpacing: 1,
                      textTransform: 'uppercase',
                      color: INK_SOFT,
                      marginBottom: 4,
                    }}
                  >
                    Drop a wine list here
                  </div>
                  <div style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: 11, color: INK_SOFT }}>
                    PDF, JPEG, or PNG · click to browse
                  </div>
                </div>
              )}
            </div>
          )}

          <Field label="Occasion" value={occasion} onChange={setOccasion} placeholder="Anniversary supper, four guests" />
          <Field label="Menu" value={menu} onChange={setMenu} placeholder="Charred ribeye · porcini · Roquefort" />
          <Field
            label="Cellar leans toward"
            value={cellarLeans}
            onChange={setCellarLeans}
            inkAccent
            placeholder="Sangiovese · Nebbiolo · old-world reds"
          />
          <Field label="Temperament" value={temperament} onChange={setTemperament} placeholder="Adventurous, within reason" />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <Field label="Ceiling" value={ceiling} onChange={setCeiling} small placeholder="$200" />
            <Field label="Bottles" value={bottles} onChange={setBottles} small placeholder="3 selections" />
          </div>

          {error && (
            <div
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: 12,
                color: OXBLOOD,
              }}
            >
              {error}
            </div>
          )}

          {import.meta.env.VITE_SHOW_DEBUG === 'true' && (
            <div>
              <div
                style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: 9,
                  letterSpacing: 3,
                  textTransform: 'uppercase',
                  color: INK_SOFT,
                  opacity: 0.85,
                  marginBottom: 4,
                }}
              >
                Test Fixture
              </div>
              <select
                value={testFixture}
                onChange={(e) => setTestFixture(e.target.value)}
                style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: 11,
                  letterSpacing: 1,
                  border: `1px solid ${INK}`,
                  padding: '6px 12px',
                  background: 'transparent',
                  color: INK,
                  cursor: 'pointer',
                  width: '100%',
                }}
              >
                <option value="">— live API —</option>
                <option value="happy">happy</option>
                <option value="sparse">sparse</option>
                <option value="long_reasoning">long_reasoning</option>
                <option value="low_confidence">low_confidence</option>
                <option value="two_wines">two_wines</option>
              </select>
            </div>
          )}

          <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: 12, color: INK_SOFT }}>
              ✦ The editor will draw from your cellar on file
            </div>
            <button
              onClick={handleSubmit}
              disabled={isLoading}
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 14,
                letterSpacing: 3,
                textTransform: 'uppercase',
                padding: '10px 22px',
                background: INK,
                color: PAPER,
                border: 'none',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.6 : 1,
              }}
            >
              {isLoading ? 'Composing…' : 'Compose the flight →'}
            </button>
          </div>
        </div>
      </div>

      {/* Footer folio band */}
      <div style={{ position: 'absolute', left: 44, right: 44, bottom: 56 }}>
        <RuleDouble color={INK} opacity={0.45} />
        <div
          style={{
            marginTop: 14,
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 18,
          }}
        >
          {FOLIO.map(([n, t, s]) => (
            <div key={n} style={{ textAlign: 'left' }}>
              <div
                style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontSize: 18,
                  fontStyle: 'italic',
                  color: OXBLOOD,
                }}
              >
                {n}
              </div>
              <div
                style={{
                  fontFamily: "'Cormorant Garamond', serif",
                  fontWeight: 500,
                  fontSize: 15,
                  color: INK,
                  letterSpacing: 0.2,
                }}
              >
                {t}
              </div>
              <div
                style={{
                  fontFamily: "'EB Garamond', serif",
                  fontStyle: 'italic',
                  fontSize: 11,
                  color: INK_SOFT,
                  marginTop: 2,
                }}
              >
                {s}
              </div>
            </div>
          ))}
        </div>
      </div>
    </PaperFrame>
  );
}
