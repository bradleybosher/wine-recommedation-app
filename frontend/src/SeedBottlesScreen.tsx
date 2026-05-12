import React, { useState } from 'react';
import { seedProfileSeedProfilePost } from './client';
import type { SeedBottle, UploadProfileResponse } from './client/types.gen';
import GlassCard from '@/components/ui/GlassCard';
import { CheckCircle2, Heart, Loader2, Plus, ThumbsDown, Trash2, Wine } from 'lucide-react';

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
      <GlassCard className="p-8">
        <div className="text-center mb-6">
          <CheckCircle2 className="mx-auto h-12 w-12 text-wine-gold mb-4" strokeWidth={1.5} />
          <h2 className="text-2xl font-bold text-white mb-1">Profile Inferred</h2>
          <p className="text-white/60 text-sm">{result.message}</p>
        </div>

        <div className="space-y-4 mb-6">
          <div className="flex items-center justify-between bg-white/5 p-4 rounded-xl">
            <span className="text-xs font-medium text-white/50 uppercase tracking-wide">Source</span>
            <span className="text-sm text-white">
              Inferred from {completedLoved.length} seed wine{completedLoved.length === 1 ? '' : 's'}
              {' · '}
              <span className="capitalize">{conf}</span> confidence
            </span>
          </div>

          {profile?.preferredStyles && profile.preferredStyles.length > 0 && (
            <div className="bg-white/5 p-4 rounded-xl">
              <p className="text-xs font-medium text-white/50 mb-2">Inferred Style Descriptors</p>
              <div className="flex flex-wrap gap-2">
                {profile.preferredStyles.map((s, i) => (
                  <span key={i} className="px-3 py-1 bg-wine-merlot/30 text-white border border-wine-rose/30 text-sm font-medium rounded-full">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {profile?.preferredGrapes && profile.preferredGrapes.length > 0 && (
            <div className="bg-white/5 p-4 rounded-xl">
              <p className="text-xs font-medium text-white/50 mb-2">Grapes</p>
              <div className="flex flex-wrap gap-2">
                {profile.preferredGrapes.map((g, i) => (
                  <span key={i} className="px-3 py-1 bg-wine-purple-mid/40 text-white border border-white/20 text-sm font-medium rounded-full capitalize">
                    {g}
                  </span>
                ))}
              </div>
            </div>
          )}

          {profile?.preferredRegions && profile.preferredRegions.length > 0 && (
            <div className="bg-white/5 p-4 rounded-xl">
              <p className="text-xs font-medium text-white/50 mb-2">Regions</p>
              <div className="flex flex-wrap gap-2">
                {profile.preferredRegions.map((r, i) => (
                  <span key={i} className="px-3 py-1 bg-wine-amber/20 text-wine-gold border border-wine-amber/30 text-sm font-medium rounded-full capitalize">
                    {r}
                  </span>
                ))}
              </div>
            </div>
          )}

          {profile?.avoidedStyles && profile.avoidedStyles.length > 0 && (
            <div className="bg-wine-burgundy/15 p-4 rounded-xl border border-wine-rose/30">
              <p className="text-xs font-medium text-wine-rose mb-2">Avoided Styles</p>
              <div className="flex flex-wrap gap-2">
                {profile.avoidedStyles.map((s, i) => (
                  <span key={i} className="px-3 py-1 bg-wine-burgundy/40 text-wine-rose border border-wine-rose/40 text-sm font-medium rounded-full">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <button
          onClick={() => onSuccess(result)}
          className="w-full flex justify-center py-3 px-4 border border-wine-rose/30 rounded-md shadow-sm text-lg font-medium text-white bg-wine-burgundy hover:bg-wine-merlot focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-wine-rose transition-colors shadow-[0_0_20px_rgba(139,37,70,0.4)]"
        >
          Continue
        </button>
      </GlassCard>
    );
  }

  const renderRow = (
    row: Row,
    list: Row[],
    setList: (rows: Row[]) => void,
    minRows: number,
  ) => (
    <div key={row._id} className="grid grid-cols-[1fr_1fr_88px_36px] gap-2 items-center">
      <input
        type="text"
        placeholder="Producer"
        value={row.producer}
        onChange={(e) => updateRow(list, setList, row._id, { producer: e.target.value })}
        className="bg-white/5 border border-white/20 rounded-md px-3 py-2 text-white placeholder-white/40 focus:outline-none focus:border-wine-rose/60 focus:ring-1 focus:ring-wine-rose/40"
      />
      <input
        type="text"
        placeholder="Wine / cuvée"
        value={row.wine}
        onChange={(e) => updateRow(list, setList, row._id, { wine: e.target.value })}
        className="bg-white/5 border border-white/20 rounded-md px-3 py-2 text-white placeholder-white/40 focus:outline-none focus:border-wine-rose/60 focus:ring-1 focus:ring-wine-rose/40"
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
        className="bg-white/5 border border-white/20 rounded-md px-3 py-2 text-white placeholder-white/40 focus:outline-none focus:border-wine-rose/60 focus:ring-1 focus:ring-wine-rose/40"
      />
      <button
        type="button"
        onClick={() => removeRow(list, setList, row._id, minRows)}
        disabled={list.length <= minRows}
        className={`flex items-center justify-center h-9 w-9 rounded-md border ${
          list.length <= minRows
            ? 'border-white/10 text-white/20 cursor-not-allowed'
            : 'border-white/20 text-white/60 hover:bg-white/10'
        }`}
        aria-label="Remove row"
      >
        <Trash2 className="h-4 w-4" strokeWidth={1.5} />
      </button>
    </div>
  );

  return (
    <GlassCard className="p-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
          <Wine className="h-6 w-6 text-wine-rose" strokeWidth={1.5} />
          Name a Few Wines You Love
        </h2>
        <p className="text-white/70">
          List 3–7 wines you have loved. We'll infer your palate from them — no CellarTracker export needed.
          Add a couple you disliked to sharpen the signal.
        </p>
      </div>

      {error && (
        <div className="bg-wine-burgundy/30 border border-wine-rose/40 text-white/90 px-4 py-3 rounded-xl mb-6">
          <strong className="font-bold">Error: </strong>
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <section>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wide flex items-center gap-2">
              <Heart className="h-4 w-4 text-wine-rose" strokeWidth={1.5} />
              Loved ({completedLoved.length}/{loved.length})
            </h3>
            <button
              type="button"
              onClick={() => loved.length < 7 && setLoved([...loved, newRow('loved')])}
              disabled={loved.length >= 7}
              className={`text-sm flex items-center gap-1 px-3 py-1 rounded-md border ${
                loved.length >= 7
                  ? 'border-white/10 text-white/30 cursor-not-allowed'
                  : 'border-white/20 text-white/80 hover:bg-white/10'
              }`}
            >
              <Plus className="h-4 w-4" strokeWidth={1.5} />
              Add
            </button>
          </div>
          <div className="space-y-2">{loved.map((r) => renderRow(r, loved, setLoved, 3))}</div>
        </section>

        <section>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wide flex items-center gap-2">
              <ThumbsDown className="h-4 w-4 text-white/60" strokeWidth={1.5} />
              Disliked (optional, max 3)
            </h3>
            <button
              type="button"
              onClick={() => disliked.length < 3 && setDisliked([...disliked, newRow('disliked')])}
              disabled={disliked.length >= 3}
              className={`text-sm flex items-center gap-1 px-3 py-1 rounded-md border ${
                disliked.length >= 3
                  ? 'border-white/10 text-white/30 cursor-not-allowed'
                  : 'border-white/20 text-white/80 hover:bg-white/10'
              }`}
            >
              <Plus className="h-4 w-4" strokeWidth={1.5} />
              Add
            </button>
          </div>
          {disliked.length === 0 ? (
            <p className="text-white/40 text-sm italic">No disliked wines added.</p>
          ) : (
            <div className="space-y-2">{disliked.map((r) => renderRow(r, disliked, setDisliked, 0))}</div>
          )}
        </section>

        <div className="flex gap-4 pt-2">
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="flex justify-center py-3 px-4 border border-white/20 rounded-md text-lg font-medium text-white/70 hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-wine-rose transition-colors"
            >
              Back
            </button>
          )}
          <button
            type="submit"
            disabled={!canSubmit}
            className={`flex-1 flex justify-center py-3 px-4 border rounded-md shadow-sm text-lg font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors ${
              !canSubmit
                ? 'bg-white/10 text-white/30 cursor-not-allowed border-white/10'
                : 'bg-wine-burgundy hover:bg-wine-merlot border-wine-rose/30 focus:ring-wine-rose shadow-[0_0_20px_rgba(139,37,70,0.4)]'
            }`}
          >
            {isLoading ? (
              <div className="flex items-center">
                <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" strokeWidth={1.5} />
                Inferring profile...
              </div>
            ) : (
              `Build Profile from ${completedLoved.length} Wine${completedLoved.length === 1 ? '' : 's'}`
            )}
          </button>
        </div>
        {completedLoved.length < 3 && (
          <p className="text-xs text-white/50 text-center">Fill in at least 3 loved wines to continue.</p>
        )}
      </form>
    </GlassCard>
  );
};

export default SeedBottlesScreen;
