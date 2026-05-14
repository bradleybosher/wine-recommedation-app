import React, { useState } from 'react';
import UploadCellarInventoryScreen from './UploadCellarInventoryScreen';
import UploadTastingHistoryScreen from './UploadTastingHistoryScreen';
import SeedBottlesScreen from './SeedBottlesScreen';
import type { UploadInventoryResponse, UploadProfileResponse } from './client/types.gen';
import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import Fleuron from '@/design/atoms/Fleuron';
import { INK, INK_SOFT, OXBLOOD, PAPER, RULE } from '@/design/tokens';

interface UploadFlowProps {
  onComplete: () => void;
}

type Pathway = 'choose' | 'cellartracker' | 'seed';
type CtStep = 'inventory' | 'profile' | 'complete';

const primaryBtn: React.CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: 14,
  letterSpacing: 3,
  textTransform: 'uppercase',
  padding: '10px 22px',
  background: INK,
  color: PAPER,
  border: `1px solid ${INK}`,
  cursor: 'pointer',
  display: 'inline-block',
};

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

const UploadFlow: React.FC<UploadFlowProps> = ({ onComplete }) => {
  const [pathway, setPathway] = useState<Pathway>('choose');
  const [ctStep, setCtStep] = useState<CtStep>('inventory');
  const [inventoryResult, setInventoryResult] = useState<UploadInventoryResponse | null>(null);
  const [profileResult, setProfileResult] = useState<UploadProfileResponse | null>(null);
  const [seedResult, setSeedResult] = useState<UploadProfileResponse | null>(null);
  const [done, setDone] = useState(false);

  const handleInventorySuccess = (result: UploadInventoryResponse) => {
    setInventoryResult(result);
    setTimeout(() => setCtStep('profile'), 1500);
  };

  const handleInventorySkip = () => {
    setCtStep('profile');
  };

  const handleProfileSuccess = (result: UploadProfileResponse) => {
    setProfileResult(result);
    setTimeout(() => setDone(true), 1500);
  };

  const handleProfileSkip = () => setDone(true);

  const handleSeedSuccess = (result: UploadProfileResponse) => {
    setSeedResult(result);
    setDone(true);
  };

  if (done) {
    const isSeed = pathway === 'seed';
    const conf = seedResult?.tasteProfile?.inferenceConfidence ?? 'medium';
    return (
      <PaperFrame>
        <Masthead dateline="Your taste profile is ready" />
        <div
          style={{
            padding: '48px 44px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 32,
          }}
        >
          <Fleuron size={32} color={OXBLOOD} />

          <div style={{ textAlign: 'center', maxWidth: 480 }}>
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 28,
                color: INK,
                letterSpacing: -0.5,
                marginBottom: 12,
              }}
            >
              {isSeed ? 'Palate Inferred' : 'Cellar Established'}
            </div>
            <div
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: 15,
                color: INK_SOFT,
                lineHeight: 1.6,
              }}
            >
              {isSeed
                ? 'Your palate has been inferred from the wines you named. Compose your first flight below.'
                : 'Your taste profile has been established from your cellar. Compose your first flight below.'}
            </div>
          </div>

          <div
            style={{
              borderTop: `1px solid ${RULE}`,
              borderBottom: `1px solid ${RULE}`,
              padding: '16px 0',
              width: '100%',
              maxWidth: 480,
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            {inventoryResult && (
              <div
                style={{
                  fontFamily: "'EB Garamond', serif",
                  fontSize: 13,
                  color: INK_SOFT,
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ fontStyle: 'italic' }}>Cellar inventory</span>
                <span>{inventoryResult.count} wines on record</span>
              </div>
            )}
            {profileResult && (
              <div
                style={{
                  fontFamily: "'EB Garamond', serif",
                  fontSize: 13,
                  color: INK_SOFT,
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ fontStyle: 'italic' }}>Tasting history</span>
                <span>Profile refined</span>
              </div>
            )}
            {seedResult && (
              <div
                style={{
                  fontFamily: "'EB Garamond', serif",
                  fontSize: 13,
                  color: INK_SOFT,
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ fontStyle: 'italic' }}>Seed bottles</span>
                <span style={{ textTransform: 'capitalize' }}>{conf} confidence</span>
              </div>
            )}
          </div>

          <button style={primaryBtn} onClick={onComplete}>
            Compose the flight →
          </button>
        </div>
      </PaperFrame>
    );
  }

  if (pathway === 'choose') {
    return (
      <PaperFrame>
        <Masthead dateline="Establish your cellar — two pathways" />

        <div style={{ padding: '0 44px 16px' }}>
          <RuleDouble color={INK} opacity={0.55} />
        </div>

        <div style={{ padding: '20px 44px', maxWidth: 700, margin: '0 auto' }}>
          <div
            style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              fontSize: 11,
              letterSpacing: 3,
              textTransform: 'uppercase',
              color: OXBLOOD,
              marginBottom: 24,
            }}
          >
            Choose your path
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            {/* CellarTracker card */}
            <button
              onClick={() => setPathway('cellartracker')}
              style={{ textAlign: 'left', background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}
            >
              <div
                style={{
                  borderTop: `2px solid ${INK}`,
                  borderLeft: `1px solid ${RULE}`,
                  borderRight: `1px solid ${RULE}`,
                  borderBottom: `1px solid ${RULE}`,
                  padding: '20px 24px',
                  transition: 'border-color 0.15s',
                }}
              >
                <div
                  style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontStyle: 'italic',
                    fontSize: 10,
                    letterSpacing: 3,
                    textTransform: 'uppercase',
                    color: OXBLOOD,
                    marginBottom: 8,
                  }}
                >
                  High confidence
                </div>
                <div
                  style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 22,
                    color: INK,
                    letterSpacing: -0.3,
                    marginBottom: 10,
                  }}
                >
                  I use CellarTracker
                </div>
                <div
                  style={{
                    fontFamily: "'EB Garamond', serif",
                    fontStyle: 'italic',
                    fontSize: 13,
                    color: INK_SOFT,
                    lineHeight: 1.6,
                  }}
                >
                  Upload your cellar inventory and tasting history TSV exports.
                  Highest-fidelity profile, grounded in your actual ratings.
                </div>
              </div>
            </button>

            {/* Seed bottles card */}
            <button
              onClick={() => setPathway('seed')}
              style={{ textAlign: 'left', background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}
            >
              <div
                style={{
                  borderTop: `2px solid ${INK}`,
                  borderLeft: `1px solid ${RULE}`,
                  borderRight: `1px solid ${RULE}`,
                  borderBottom: `1px solid ${RULE}`,
                  padding: '20px 24px',
                }}
              >
                <div
                  style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontStyle: 'italic',
                    fontSize: 10,
                    letterSpacing: 3,
                    textTransform: 'uppercase',
                    color: INK_SOFT,
                    marginBottom: 8,
                    opacity: 0.75,
                  }}
                >
                  Medium confidence
                </div>
                <div
                  style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 22,
                    color: INK,
                    letterSpacing: -0.3,
                    marginBottom: 10,
                  }}
                >
                  Name a few wines I love
                </div>
                <div
                  style={{
                    fontFamily: "'EB Garamond', serif",
                    fontStyle: 'italic',
                    fontSize: 13,
                    color: INK_SOFT,
                    lineHeight: 1.6,
                  }}
                >
                  Tell us 3–7 wines you have loved (and a few you disliked).
                  We'll infer your palate in 60 seconds — no exports required.
                </div>
              </div>
            </button>
          </div>
        </div>
      </PaperFrame>
    );
  }

  if (pathway === 'seed') {
    return (
      <PaperFrame>
        <Masthead small dateline="Name the wines that shaped your palate" />
        <div style={{ padding: '0 44px 16px' }}>
          <RuleDouble color={INK} opacity={0.55} />
        </div>
        <div style={{ padding: '8px 44px' }}>
          <button style={ghostBtn} onClick={() => setPathway('choose')}>
            ← Change pathway
          </button>
        </div>
        <div style={{ padding: '16px 44px' }}>
          <SeedBottlesScreen onSuccess={handleSeedSuccess} onBack={() => setPathway('choose')} />
        </div>
      </PaperFrame>
    );
  }

  // CellarTracker pathway
  return (
    <PaperFrame>
      <Masthead small dateline="Upload your CellarTracker exports" />
      <div style={{ padding: '0 44px 16px' }}>
        <RuleDouble color={INK} opacity={0.55} />
      </div>

      {/* Step indicator */}
      <div style={{ padding: '12px 44px', display: 'flex', alignItems: 'center', gap: 0 }}>
        {['Cellar', 'Refine', 'Compose'].map((label, idx) => {
          const stepDone =
            (idx === 0 && !!inventoryResult) ||
            (idx === 1 && !!profileResult);
          const stepActive =
            (idx === 0 && ctStep === 'inventory') ||
            (idx === 1 && ctStep === 'profile');
          return (
            <React.Fragment key={label}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <div
                  style={{
                    width: 24,
                    height: 24,
                    borderRadius: '50%',
                    border: `1px solid ${stepActive || stepDone ? INK : RULE}`,
                    background: stepDone ? INK : 'transparent',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 11,
                    color: stepDone ? PAPER : stepActive ? INK : INK_SOFT,
                    opacity: stepActive || stepDone ? 1 : 0.5,
                  }}
                >
                  {stepDone ? '✓' : idx + 1}
                </div>
                <span
                  style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 10,
                    letterSpacing: 2,
                    textTransform: 'uppercase',
                    color: stepActive ? INK : INK_SOFT,
                    opacity: stepActive || stepDone ? 1 : 0.5,
                  }}
                >
                  {label}
                </span>
              </div>
              {idx < 2 && (
                <div
                  style={{
                    flex: 1,
                    height: 1,
                    background: RULE,
                    marginBottom: 20,
                    marginLeft: 8,
                    marginRight: 8,
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      <div style={{ padding: '4px 44px' }}>
        <button style={ghostBtn} onClick={() => setPathway('choose')}>
          ← Change pathway
        </button>
      </div>

      <div style={{ padding: '16px 44px' }}>
        {ctStep === 'inventory' && (
          <UploadCellarInventoryScreen
            onSuccess={handleInventorySuccess}
            onSkip={handleInventorySkip}
          />
        )}
        {ctStep === 'profile' && (
          <UploadTastingHistoryScreen
            onSuccess={handleProfileSuccess}
            onSkip={handleProfileSkip}
          />
        )}
      </div>
    </PaperFrame>
  );
};

export default UploadFlow;
