import React, { useState } from 'react';
import { seedProfileSeedProfilePost } from './client';
import type { SeedBottle, UploadProfileResponse } from './client/types.gen';
import { INK, INK_SOFT, OXBLOOD, PAPER, RULE } from '@/design/tokens';
import { Loader2, Plus, Trash2 } from 'lucide-react';

interface SeedBottlesScreenProps {
  onSuccess: (response: UploadProfileResponse) => void;
  onBack?: () => void;
}

type Row = SeedBottle & { _id: number };

let _rowIdCounter = 0;
const newRow = (sentiment: 'loved' | 'disliked'): Row => ({
  _id: ++_rowIdCounter,
  producer: '',
  wine: '',
  vintage: null,
  sentiment,
});

const submitBtn = (enabled: boolean): React.CSSProperties => ({
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: 14,
  letterSpacing: 3,
  textTransform: 'uppercase',
  padding: '10px 22px',
  background: enabled ? INK : 'transparent',
  color: enabled ? PAPER : INK,
  border: `1px solid ${INK}`,
  cursor: enabled ? 'pointer' : 'not-allowed',
  opacity: enabled ? 1 : 0.4,
  flex: 1,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 8,
});

const inputStyle: React.CSSProperties = {
  fontFamily: "'EB Garamond', serif",
  fontSize: 14,
  padding: '6px 10px',
  border: `1px solid ${RULE}`,
  background: 'transparent',
  color: INK,
  outline: 'none',
  width: '100%',
  boxSizing: 'border-box',
};

const tagStyle: React.CSSProperties = {
  fontFamily: "'EB Garamond', serif",
  fontSize: 12,
  padding: '2px 8px',
  border: `1px solid ${RULE}`,
  color: INK_SOFT,
};

const SeedBottlesScreen: React.FC<SeedBottlesScreenProps> = ({ onSuccess, onBack }) => {
  const [loved, setLoved] = useState<Row[]>(() => [newRow('loved'), newRow('loved'), newRow('loved')]);
  const [disliked, setDisliked] = useState<Row[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<UploadProfileResponse | null>(null);

  const completedLoved = loved.filter((r) => r.producer.trim() && r.wine.trim());
  const canSubmit = completedLoved.length >= 3 && !isLoading;

  const updateRow = (
    list: Row[],
    setList: (rows: Row[]) => void,
    id: number,
    patch: Partial<SeedBottle>,
  ) => {
    setList(list.map((r) => (r._id === id ? { ...r, ...patch } : r)));
  };

  const removeRow = (list: Row[], setList: (rows: Row[]) => void, id: number, min: number) => {
    if (list.length <= min) return;
    setList(list.filter((r) => r._id !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setIsLoading(true);
    setError('');

    const stripRow = (r: Row): SeedBottle => ({
      producer: r.producer.trim(),
      wine: r.wine.trim(),
      vintage: r.vintage || null,
      sentiment: r.sentiment,
      note: r.note?.trim() || null,
    });

    try {
      const response = await seedProfileSeedProfilePost({
        body: {
          loved: completedLoved.map(stripRow),
          disliked: disliked
            .filter((r) => r.producer.trim() && r.wine.trim())
            .map(stripRow),
        },
      });
      if (response && response.data) {
        setResult(response.data);
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err: any) {
      const detail = err?.data?.detail;
      const msg = Array.isArray(detail) ? detail.map((d: any) => d.msg).join('; ') : detail;
      setError(msg || (err instanceof Error ? err.message : 'Failed to build profile from seed bottles'));
    } finally {
      setIsLoading(false);
    }
  };

  if (result) {
    const profile = result.tasteProfile;
    const conf = profile?.inferenceConfidence ?? 'medium';
    return (
      <div
        style={{
          border: `1px solid ${RULE}`,
          padding: '28px 28px',
          background: 'rgba(243,232,212,0.4)',
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
            marginBottom: 12,
          }}
        >
          Profile Inferred
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              borderBottom: `1px solid ${RULE}`,
              paddingBottom: 10,
            }}
          >
            <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: INK_SOFT }}>
              Source
            </span>
            <span style={{ fontFamily: "'EB Garamond', serif", fontSize: 13, color: INK_SOFT, fontStyle: 'italic' }}>
              {completedLoved.length} seed wine{completedLoved.length === 1 ? '' : 's'} · {conf} confidence
            </span>
          </div>

          {profile?.preferredStyles && profile.preferredStyles.length > 0 && (
            <div>
              <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 6 }}>Style</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {profile.preferredStyles.map((s, i) => (
                  <span key={i} style={tagStyle}>{s}</span>
                ))}
              </div>
            </div>
          )}

          {profile?.preferredGrapes && profile.preferredGrapes.length > 0 && (
            <div>
              <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 6 }}>Grapes</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {profile.preferredGrapes.map((g, i) => (
                  <span key={i} style={tagStyle}>{g}</span>
                ))}
              </div>
            </div>
          )}

          {profile?.preferredRegions && profile.preferredRegions.length > 0 && (
            <div>
              <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 6 }}>Regions</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {profile.preferredRegions.map((r, i) => (
                  <span key={i} style={tagStyle}>{r}</span>
                ))}
              </div>
            </div>
          )}

          {profile?.avoidedStyles && profile.avoidedStyles.length > 0 && (
            <div>
              <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: OXBLOOD, marginBottom: 6 }}>Avoided</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {profile.avoidedStyles.map((s, i) => (
                  <span key={i} style={{ ...tagStyle, borderColor: OXBLOOD, color: OXBLOOD }}>{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        <button onClick={() => onSuccess(result)} style={submitBtn(true)}>
          Continue
        </button>
      </div>
    );
  }

  const renderRow = (
    row: Row,
    list: Row[],
    setList: (rows: Row[]) => void,
    minRows: number,
  ) => (
    <div
      key={row._id}
      style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 88px 32px', gap: 8, alignItems: 'center' }}
    >
      <input
        type="text"
        placeholder="Producer"
        value={row.producer}
        onChange={(e) => updateRow(list, setList, row._id, { producer: e.target.value })}
        style={inputStyle}
      />
      <input
        type="text"
        placeholder="Wine / cuvée"
        value={row.wine}
        onChange={(e) => updateRow(list, setList, row._id, { wine: e.target.value })}
        style={inputStyle}
      />
      <input
        type="number"
        placeholder="Vintage"
        value={row.vintage ?? ''}
        onChange={(e) =>
          updateRow(list, setList, row._id, {
            vintage: e.target.value ? Number(e.target.value) : null,
          })
        }
        style={inputStyle}
      />
      <button
        type="button"
        onClick={() => removeRow(list, setList, row._id, minRows)}
        disabled={list.length <= minRows}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 32,
          height: 32,
          border: `1px solid ${RULE}`,
          background: 'transparent',
          cursor: list.length <= minRows ? 'not-allowed' : 'pointer',
          opacity: list.length <= minRows ? 0.3 : 0.6,
          color: INK,
        }}
        aria-label="Remove row"
      >
        <Trash2 style={{ width: 14, height: 14 }} strokeWidth={1.5} />
      </button>
    </div>
  );

  const addBtn = (disabled: boolean): React.CSSProperties => ({
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: 11,
    letterSpacing: 2,
    textTransform: 'uppercase',
    padding: '4px 10px',
    background: 'transparent',
    color: disabled ? INK_SOFT : INK,
    border: `1px solid ${disabled ? RULE : INK}`,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.4 : 1,
    display: 'flex',
    alignItems: 'center',
    gap: 4,
  });

  return (
    <div>
      {error && (
        <div
          style={{
            border: `1px solid ${RULE}`,
            padding: '10px 16px',
            marginBottom: 16,
            fontFamily: "'EB Garamond', serif",
            fontSize: 13,
            color: OXBLOOD,
          }}
        >
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {/* Loved section */}
        <section>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: `1px solid ${RULE}`,
              paddingBottom: 8,
              marginBottom: 12,
            }}
          >
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 10,
                letterSpacing: 3,
                textTransform: 'uppercase',
                color: OXBLOOD,
              }}
            >
              Loved · {completedLoved.length}/{loved.length}
            </div>
            <button
              type="button"
              onClick={() => loved.length < 7 && setLoved([...loved, newRow('loved')])}
              disabled={loved.length >= 7}
              style={addBtn(loved.length >= 7)}
            >
              <Plus style={{ width: 12, height: 12 }} strokeWidth={1.5} />
              Add
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {loved.map((r) => renderRow(r, loved, setLoved, 3))}
          </div>
        </section>

        {/* Disliked section */}
        <section>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: `1px solid ${RULE}`,
              paddingBottom: 8,
              marginBottom: 12,
            }}
          >
            <div
              style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 10,
                letterSpacing: 3,
                textTransform: 'uppercase',
                color: INK_SOFT,
                opacity: 0.7,
              }}
            >
              Disliked · optional, max 3
            </div>
            <button
              type="button"
              onClick={() => disliked.length < 3 && setDisliked([...disliked, newRow('disliked')])}
              disabled={disliked.length >= 3}
              style={addBtn(disliked.length >= 3)}
            >
              <Plus style={{ width: 12, height: 12 }} strokeWidth={1.5} />
              Add
            </button>
          </div>
          {disliked.length === 0 ? (
            <div
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: 13,
                color: INK_SOFT,
                opacity: 0.6,
              }}
            >
              No disliked wines added.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {disliked.map((r) => renderRow(r, disliked, setDisliked, 0))}
            </div>
          )}
        </section>

        <div style={{ display: 'flex', gap: 12, paddingTop: 4 }}>
          <button
            type="submit"
            disabled={!canSubmit}
            style={submitBtn(canSubmit)}
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" style={{ width: 16, height: 16 }} strokeWidth={1.5} />
                Inferring profile…
              </>
            ) : (
              `Build Profile from ${completedLoved.length} Wine${completedLoved.length === 1 ? '' : 's'}`
            )}
          </button>
        </div>

        {completedLoved.length < 3 && (
          <div
            style={{
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: 12,
              color: INK_SOFT,
              textAlign: 'center',
              opacity: 0.7,
            }}
          >
            Fill in at least 3 loved wines to continue.
          </div>
        )}
      </form>
    </div>
  );
};

export default SeedBottlesScreen;
