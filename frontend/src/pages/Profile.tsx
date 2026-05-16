import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2, Pencil } from 'lucide-react';

import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import { INK, INK_SOFT, OXBLOOD, PAPER, RULE, lineHeight, space, typeScale } from '@/design/tokens';

import {
  patchProfileProfilePatch,
  profileSummaryProfileSummaryGet,
  revertProfileProfileRevertPost,
} from '@/client';
import type {
  ProfilePatchRequest,
  ProfileSummaryResponse,
  TasteMarkers,
} from '@/client/types.gen';

import UploadCellarInventoryScreen from '@/UploadCellarInventoryScreen';
import UploadTastingHistoryScreen from '@/UploadTastingHistoryScreen';
import SeedBottlesScreen from '@/SeedBottlesScreen';

type StartOverMode = 'none' | 'cellar' | 'seed';

interface EditState {
  topVarietals: string;
  topRegions: string;
  preferredDescriptors: string;
  avoidedStyles: string;
  avgSpend: string;
  styleSummary: string;
  taste: TasteMarkers;
}

const MARKER_LABELS: Record<number, string> = {
  1: 'Very Low',
  2: 'Low',
  3: 'Medium',
  4: 'High',
  5: 'Very High',
};

const DEFAULT_MARKERS: TasteMarkers = { acidity: 3, tannin: 3, body: 3, oak: 3 };

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

const dangerBtn: React.CSSProperties = {
  ...ghostBtn,
  color: OXBLOOD,
  borderColor: OXBLOOD,
};

const inputStyle: React.CSSProperties = {
  fontFamily: "'EB Garamond', serif",
  fontSize: typeScale.body,
  color: INK,
  background: 'transparent',
  border: `1px solid ${RULE}`,
  padding: `${space.xs} ${space.xs}`,
  width: '100%',
  outline: 'none',
};

const sectionHeading = (label: string): React.ReactElement => (
  <div
    style={{
      fontFamily: "'Cormorant Garamond', serif",
      fontStyle: 'italic',
      fontSize: typeScale.micro,
      letterSpacing: 3,
      textTransform: 'uppercase',
      color: OXBLOOD,
      marginBottom: 12,
    }}
  >
    {label}
  </div>
);

const tagStyle: React.CSSProperties = {
  fontFamily: "'EB Garamond', serif",
  fontSize: typeScale.label,
  padding: '2px 8px',
  border: `1px solid ${RULE}`,
  color: INK_SOFT,
};

function markerPercent(v: number): number {
  return Math.round((Math.max(1, Math.min(5, v)) / 5) * 100);
}

function markerLabel(v: number): string {
  return MARKER_LABELS[Math.round(v)] ?? 'Medium';
}

function joinList(xs: string[] | null | undefined): string {
  return (xs ?? []).join(', ');
}

function splitList(s: string): string[] {
  return s
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean);
}

function arraysEqual(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i += 1) if (a[i] !== b[i]) return false;
  return true;
}

function summaryToEditState(s: ProfileSummaryResponse): EditState {
  return {
    topVarietals: joinList(s.topVarietals),
    topRegions: joinList(s.topRegions),
    preferredDescriptors: joinList(s.preferredDescriptors),
    avoidedStyles: joinList(s.avoidedStyles),
    avgSpend: s.avgSpend != null ? String(s.avgSpend) : '',
    styleSummary: s.styleSummary ?? '',
    taste: s.tasteMarkers ?? DEFAULT_MARKERS,
  };
}

function diffEdits(
  draft: EditState,
  original: EditState,
): ProfilePatchRequest {
  const patch: ProfilePatchRequest = {};

  const draftVarietals = splitList(draft.topVarietals);
  if (!arraysEqual(draftVarietals, splitList(original.topVarietals))) {
    patch.topVarietals = draftVarietals;
  }

  const draftRegions = splitList(draft.topRegions);
  if (!arraysEqual(draftRegions, splitList(original.topRegions))) {
    patch.topRegions = draftRegions;
  }

  const draftDescriptors = splitList(draft.preferredDescriptors);
  if (!arraysEqual(draftDescriptors, splitList(original.preferredDescriptors))) {
    patch.preferredDescriptors = draftDescriptors;
  }

  const draftAvoided = splitList(draft.avoidedStyles);
  if (!arraysEqual(draftAvoided, splitList(original.avoidedStyles))) {
    patch.avoidedStyles = draftAvoided;
  }

  if (draft.avgSpend !== original.avgSpend) {
    const parsed = draft.avgSpend.trim() ? Number(draft.avgSpend.trim()) : NaN;
    if (Number.isFinite(parsed)) patch.avgSpend = Math.round(parsed);
  }

  if (draft.styleSummary !== original.styleSummary) {
    patch.styleSummary = draft.styleSummary;
  }

  const tasteDiff =
    draft.taste.acidity !== original.taste.acidity ||
    draft.taste.tannin !== original.taste.tannin ||
    draft.taste.body !== original.taste.body ||
    draft.taste.oak !== original.taste.oak;
  if (tasteDiff) patch.tasteMarkers = draft.taste;

  return patch;
}

interface MarkerEditorProps {
  label: string;
  value: number;
  editing: boolean;
  onChange: (v: number) => void;
}

const MarkerEditor: React.FC<MarkerEditorProps> = ({ label, value, editing, onChange }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
    <span
      style={{
        width: 72,
        fontFamily: "'Cormorant Garamond', serif",
        fontSize: typeScale.label,
        letterSpacing: 1,
        textTransform: 'uppercase',
        color: INK_SOFT,
        flexShrink: 0,
      }}
    >
      {label}
    </span>
    <div style={{ flex: 1, height: 2, background: RULE, overflow: 'hidden' }}>
      <div
        style={{
          height: '100%',
          width: `${markerPercent(value)}%`,
          background: INK,
          transition: 'width 0.3s ease',
        }}
      />
    </div>
    {editing ? (
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{
          ...inputStyle,
          width: 96,
          padding: '2px 6px',
          fontSize: typeScale.label,
        }}
      >
        {[1, 2, 3, 4, 5].map((n) => (
          <option key={n} value={n}>
            {n} · {MARKER_LABELS[n]}
          </option>
        ))}
      </select>
    ) : (
      <span
        style={{
          width: 96,
          fontFamily: "'EB Garamond', serif",
          fontStyle: 'italic',
          fontSize: typeScale.label,
          color: INK_SOFT,
          textAlign: 'right',
          flexShrink: 0,
        }}
      >
        {markerLabel(value)}
      </span>
    )}
  </div>
);

const Section: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ borderTop: `1px solid ${RULE}`, paddingTop: 20, paddingBottom: 20 }}>
    {children}
  </div>
);

const FieldRow: React.FC<{
  label: string;
  editing: boolean;
  display: React.ReactNode;
  editor: React.ReactNode;
}> = ({ label, editing, display, editor }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
    <div
      style={{
        fontFamily: "'Cormorant Garamond', serif",
        fontSize: typeScale.micro,
        letterSpacing: 2,
        textTransform: 'uppercase',
        color: INK_SOFT,
      }}
    >
      {label}
    </div>
    {editing ? editor : display}
  </div>
);

const Profile: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<ProfileSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<EditState | null>(null);
  const [original, setOriginal] = useState<EditState | null>(null);
  const [saving, setSaving] = useState(false);

  const [startOver, setStartOver] = useState<StartOverMode>('none');
  const [reverting, setReverting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await profileSummaryProfileSummaryGet();
      const summary = res.data ?? null;
      setData(summary);
      if (summary) {
        const initial = summaryToEditState(summary);
        setDraft(initial);
        setOriginal(initial);
      }
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleCancel = () => {
    if (original) setDraft(original);
    setEditing(false);
  };

  const handleSave = async () => {
    if (!draft || !original) return;
    const patch = diffEdits(draft, original);
    if (Object.keys(patch).length === 0) {
      setEditing(false);
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const res = await patchProfileProfilePatch({ body: patch });
      const summary = res.data ?? null;
      if (summary) {
        setData(summary);
        const next = summaryToEditState(summary);
        setDraft(next);
        setOriginal(next);
      }
      setEditing(false);
      setNotice('Palate updated.');
      setTimeout(() => setNotice(null), 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save.');
    } finally {
      setSaving(false);
    }
  };

  const handleRevert = async () => {
    if (!window.confirm('Revert to the last automatic backup? Any manual edits will be lost.')) {
      return;
    }
    setReverting(true);
    setError(null);
    try {
      await revertProfileProfileRevertPost();
      await refresh();
      setNotice('Profile reverted to the last backup.');
      setTimeout(() => setNotice(null), 2500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Revert failed.');
    } finally {
      setReverting(false);
    }
  };

  const sourceLabel = useMemo(() => {
    const src = data?.profileSource;
    if (src === 'seed_bottles') {
      const conf = data?.inferenceConfidence;
      const count = data?.seedBottleCount;
      return `Seeded from ${count ?? '—'} bottles · ${conf ?? 'medium'} confidence`;
    }
    if (src === 'cellartracker') return 'Derived from CellarTracker export';
    return 'Manual profile';
  }, [data]);

  if (startOver !== 'none') {
    return (
      <PaperFrame>
        <Masthead
          small
          dateline={
            startOver === 'seed'
              ? 'Re-seed your palate from a few wines'
              : 'Re-upload your CellarTracker exports'
          }
        />
        <div style={{ padding: `0 0 ${space.sm}` }}>
          <RuleDouble color={INK} opacity={0.55} />
        </div>
        <div style={{ padding: `${space.xs} 0` }}>
          <button style={ghostBtn} onClick={() => setStartOver('none')}>
            ← Back to your palate
          </button>
        </div>
        <div style={{ padding: `${space.sm} 0 ${space.xl}` }}>
          {startOver === 'seed' ? (
            <SeedBottlesScreen
              onSuccess={async () => {
                await refresh();
                setStartOver('none');
                setNotice('New palate inferred from your seed bottles.');
                setTimeout(() => setNotice(null), 2500);
              }}
              onBack={() => setStartOver('none')}
            />
          ) : (
            <CellarReuploadFlow
              onDone={async () => {
                await refresh();
                setStartOver('none');
                setNotice('Profile rebuilt from your CellarTracker export.');
                setTimeout(() => setNotice(null), 2500);
              }}
            />
          )}
        </div>
      </PaperFrame>
    );
  }

  return (
    <PaperFrame>
      <Masthead dateline="Your palate, with a hand at the dial" />

      <div style={{ padding: `0 0 ${space.xs}` }}>
        <RuleDouble color={INK} opacity={0.45} />
      </div>

      <div style={{ padding: `${space.sm} 0 ${space.xl}`, maxWidth: 880, margin: '0 auto' }}>
        {/* Top bar: back link + edit/save actions */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 8,
          }}
        >
          <Link
            to="/preferences"
            style={{
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.body,
              color: INK_SOFT,
              textDecoration: 'none',
            }}
          >
            ← Back to the editor's desk
          </Link>
          {data && !editing && (
            <button
              style={ghostBtn}
              onClick={() => setEditing(true)}
              aria-label="Edit palate"
            >
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Pencil size={12} strokeWidth={1.5} /> Edit
              </span>
            </button>
          )}
          {data && editing && (
            <div style={{ display: 'flex', gap: 8 }}>
              <button style={ghostBtn} onClick={handleCancel} disabled={saving}>
                Cancel
              </button>
              <button style={primaryBtn} onClick={handleSave} disabled={saving}>
                {saving ? (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <Loader2 size={12} strokeWidth={1.5} className="animate-spin" /> Saving…
                  </span>
                ) : (
                  'Save'
                )}
              </button>
            </div>
          )}
        </div>

        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.body,
            color: INK_SOFT,
            marginBottom: 4,
          }}
        >
          {sourceLabel}
        </div>

        {notice && (
          <div
            style={{
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.body,
              color: INK,
              borderTop: `1px solid ${RULE}`,
              borderBottom: `1px solid ${RULE}`,
              padding: '6px 0',
              margin: '8px 0',
            }}
          >
            {notice}
          </div>
        )}

        {error && (
          <div
            style={{
              fontFamily: "'EB Garamond', serif",
              fontSize: typeScale.body,
              color: OXBLOOD,
              padding: '6px 10px',
              border: `1px solid ${OXBLOOD}`,
              margin: '8px 0',
            }}
          >
            {error}
          </div>
        )}

        {loading && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '60px 0',
              gap: 12,
            }}
          >
            <Loader2 size={28} strokeWidth={1.5} className="animate-spin" style={{ color: INK_SOFT }} />
            <div
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: typeScale.body,
                color: INK_SOFT,
              }}
            >
              Pouring your palate…
            </div>
          </div>
        )}

        {data && draft && !loading && (
          <>
            {/* Palate portrait / style summary */}
            <Section>
              {sectionHeading('Palate Portrait')}
              <FieldRow
                label="One-sentence portrait"
                editing={editing}
                display={
                  data.styleSummary ? (
                    <div
                      style={{
                        fontFamily: "'EB Garamond', serif",
                        fontStyle: 'italic',
                        fontSize: typeScale.bodyLg,
                        color: INK,
                        lineHeight: lineHeight.body,
                      }}
                    >
                      "{data.styleSummary}"
                    </div>
                  ) : (
                    <div
                      style={{
                        fontFamily: "'EB Garamond', serif",
                        fontStyle: 'italic',
                        fontSize: typeScale.body,
                        color: INK_SOFT,
                        opacity: 0.6,
                      }}
                    >
                      No portrait yet — edit to write your own.
                    </div>
                  )
                }
                editor={
                  <textarea
                    value={draft.styleSummary}
                    onChange={(e) => setDraft({ ...draft, styleSummary: e.target.value })}
                    rows={3}
                    style={{ ...inputStyle, resize: 'vertical' as const, lineHeight: 1.5 }}
                    placeholder="A single line capturing your overall palate."
                  />
                }
              />
            </Section>

            {/* Taste markers */}
            <Section>
              {sectionHeading('Taste Profile')}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {(['acidity', 'tannin', 'body', 'oak'] as const).map((key) => (
                  <MarkerEditor
                    key={key}
                    label={key.charAt(0).toUpperCase() + key.slice(1)}
                    value={draft.taste[key]}
                    editing={editing}
                    onChange={(v) => setDraft({ ...draft, taste: { ...draft.taste, [key]: v } })}
                  />
                ))}
              </div>
              <div
                style={{
                  fontFamily: "'EB Garamond', serif",
                  fontStyle: 'italic',
                  fontSize: typeScale.label,
                  color: INK_SOFT,
                  marginTop: 12,
                  opacity: 0.6,
                }}
              >
                {editing
                  ? 'Set explicit marker values — these override the heuristic derivation.'
                  : 'Indicative, not prescriptive — set them yourself if you disagree.'}
              </div>
            </Section>

            {/* Flavour preferences */}
            <Section>
              {sectionHeading('Flavour Preferences')}
              <FieldRow
                label="Comma-separated descriptors"
                editing={editing}
                display={
                  (data.preferredDescriptors?.length ?? 0) > 0 ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {data.preferredDescriptors!.map((d, i) => (
                        <span key={i} style={tagStyle}>
                          {d}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <div style={{ ...tagStyle, opacity: 0.5 }}>—</div>
                  )
                }
                editor={
                  <input
                    type="text"
                    value={draft.preferredDescriptors}
                    onChange={(e) => setDraft({ ...draft, preferredDescriptors: e.target.value })}
                    style={inputStyle}
                    placeholder="taut mineral whites, savoury earth, fine tannin"
                  />
                }
              />
            </Section>

            {/* Styles to avoid */}
            <Section>
              {sectionHeading('Styles to Avoid')}
              <FieldRow
                label="Comma-separated"
                editing={editing}
                display={
                  (data.avoidedStyles?.length ?? 0) > 0 ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {data.avoidedStyles!.map((s, i) => (
                        <span
                          key={i}
                          style={{ ...tagStyle, borderColor: OXBLOOD, color: OXBLOOD }}
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <div style={{ ...tagStyle, opacity: 0.5 }}>—</div>
                  )
                }
                editor={
                  <input
                    type="text"
                    value={draft.avoidedStyles}
                    onChange={(e) => setDraft({ ...draft, avoidedStyles: e.target.value })}
                    style={inputStyle}
                    placeholder="heavily oaked reds, sweet fruit-forward styles"
                  />
                }
              />
            </Section>

            {/* Varietals + regions */}
            <Section>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                <div>
                  {sectionHeading('Top Varietals')}
                  <FieldRow
                    label="Comma-separated"
                    editing={editing}
                    display={
                      (data.topVarietals?.length ?? 0) > 0 ? (
                        <ol style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                          {data.topVarietals!.map((v, i) => (
                            <li key={i} style={{ display: 'flex', gap: 10 }}>
                              <span
                                style={{
                                  fontFamily: "'Cormorant Garamond', serif",
                                  fontSize: typeScale.label,
                                  color: INK_SOFT,
                                  width: 16,
                                  flexShrink: 0,
                                }}
                              >
                                {i + 1}
                              </span>
                              <span style={{ fontFamily: "'EB Garamond', serif", fontSize: typeScale.body, color: INK }}>
                                {v}
                              </span>
                            </li>
                          ))}
                        </ol>
                      ) : (
                        <div style={{ ...tagStyle, opacity: 0.5 }}>—</div>
                      )
                    }
                    editor={
                      <input
                        type="text"
                        value={draft.topVarietals}
                        onChange={(e) => setDraft({ ...draft, topVarietals: e.target.value })}
                        style={inputStyle}
                        placeholder="pinot noir, chardonnay, nebbiolo"
                      />
                    }
                  />
                </div>

                <div>
                  {sectionHeading('Top Regions')}
                  <FieldRow
                    label="Comma-separated"
                    editing={editing}
                    display={
                      (data.topRegions?.length ?? 0) > 0 ? (
                        <ol style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                          {data.topRegions!.map((r, i) => (
                            <li key={i} style={{ display: 'flex', gap: 10 }}>
                              <span
                                style={{
                                  fontFamily: "'Cormorant Garamond', serif",
                                  fontSize: typeScale.label,
                                  color: INK_SOFT,
                                  width: 16,
                                  flexShrink: 0,
                                }}
                              >
                                {i + 1}
                              </span>
                              <span style={{ fontFamily: "'EB Garamond', serif", fontSize: typeScale.body, color: INK }}>
                                {r}
                              </span>
                            </li>
                          ))}
                        </ol>
                      ) : (
                        <div style={{ ...tagStyle, opacity: 0.5 }}>—</div>
                      )
                    }
                    editor={
                      <input
                        type="text"
                        value={draft.topRegions}
                        onChange={(e) => setDraft({ ...draft, topRegions: e.target.value })}
                        style={inputStyle}
                        placeholder="burgundy, piedmont, loire"
                      />
                    }
                  />
                </div>
              </div>
            </Section>

            {/* Average spend */}
            <Section>
              {sectionHeading('Average Bottle Spend')}
              <FieldRow
                label="Whole dollars"
                editing={editing}
                display={
                  data.avgSpend != null ? (
                    <div
                      style={{
                        fontFamily: "'Cormorant Garamond', serif",
                        fontSize: typeScale.h1,
                        color: INK,
                        letterSpacing: -0.5,
                      }}
                    >
                      ${data.avgSpend}
                    </div>
                  ) : (
                    <div style={{ ...tagStyle, opacity: 0.5 }}>—</div>
                  )
                }
                editor={
                  <input
                    type="number"
                    inputMode="numeric"
                    value={draft.avgSpend}
                    onChange={(e) => setDraft({ ...draft, avgSpend: e.target.value })}
                    style={{ ...inputStyle, width: 140 }}
                    placeholder="45"
                  />
                }
              />
            </Section>

            {/* Start over */}
            <Section>
              {sectionHeading('Start Over')}
              <div
                style={{
                  fontFamily: "'EB Garamond', serif",
                  fontStyle: 'italic',
                  fontSize: typeScale.body,
                  color: INK_SOFT,
                  marginBottom: 12,
                  lineHeight: lineHeight.body,
                }}
              >
                Replace the underlying profile entirely. Re-running either intake clears any manual edits you've made above.
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                <button style={ghostBtn} onClick={() => setStartOver('cellar')}>
                  Re-upload CellarTracker
                </button>
                <button style={ghostBtn} onClick={() => setStartOver('seed')}>
                  Re-seed from wines
                </button>
                <button style={dangerBtn} onClick={handleRevert} disabled={reverting}>
                  {reverting ? 'Reverting…' : 'Revert to last backup'}
                </button>
                <button style={ghostBtn} onClick={() => navigate('/preferences')}>
                  Compose a flight →
                </button>
              </div>
            </Section>
          </>
        )}
      </div>
    </PaperFrame>
  );
};

// ── Re-upload sub-flow ───────────────────────────────────────────────────────

const CellarReuploadFlow: React.FC<{ onDone: () => void }> = ({ onDone }) => {
  const [step, setStep] = useState<'inventory' | 'tasting' | 'done'>('inventory');

  useEffect(() => {
    if (step === 'done') onDone();
  }, [step, onDone]);

  if (step === 'done') return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div
        style={{
          fontFamily: "'EB Garamond', serif",
          fontStyle: 'italic',
          fontSize: typeScale.body,
          color: INK_SOFT,
        }}
      >
        Step {step === 'inventory' ? '1' : '2'} of 2 — {step === 'inventory' ? 'cellar inventory' : 'tasting history'}
      </div>
      {step === 'inventory' ? (
        <UploadCellarInventoryScreen
          onSuccess={() => setStep('tasting')}
          onSkip={() => setStep('tasting')}
        />
      ) : (
        <UploadTastingHistoryScreen
          onSuccess={() => setStep('done')}
          onSkip={() => setStep('done')}
        />
      )}
    </div>
  );
};

export default Profile;
