import React, { useEffect, useState } from 'react';
import { profileSummaryProfileSummaryGet } from '@/client';
import type { ProfileSummaryResponse, TasteMarkers } from '@/client/types.gen';
import GlassCard from '@/components/ui/GlassCard';
import {
  BookOpen,
  Wine,
  MapPin,
  Loader2,
  ThumbsDown,
  Sparkles,
  LayoutGrid,
} from 'lucide-react';

// ─── Helpers ────────────────────────────────────────────────────────────────

const MARKER_LABELS: Record<number, string> = {
  1: 'Very Low',
  2: 'Low',
  3: 'Medium',
  4: 'High',
  5: 'Very High',
};

function markerLabel(val: number): string {
  return MARKER_LABELS[Math.round(val)] ?? 'Medium';
}

function markerPercent(val: number): number {
  return Math.round((val / 5) * 100);
}

// ─── Sub-components ──────────────────────────────────────────────────────────

interface MarkerBarProps {
  label: string;
  value: number;
}

const MarkerBar: React.FC<MarkerBarProps> = ({ label, value }) => (
  <div className="flex items-center gap-3">
    <span className="w-20 text-sm text-white/70 shrink-0">{label}</span>
    <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
      <div
        className="h-full rounded-full bg-wine-rose/70 transition-all duration-500"
        style={{ width: `${markerPercent(value)}%` }}
      />
    </div>
    <span className="w-20 text-xs text-white/50 text-right shrink-0">
      {markerLabel(value)}
    </span>
  </div>
);

interface StatCardProps {
  label: string;
  value: string | number;
}

const StatCard: React.FC<StatCardProps> = ({ label, value }) => (
  <GlassCard className="p-4 text-center">
    <div className="text-3xl font-bold text-white mb-1">{value}</div>
    <div className="text-xs text-white/60 uppercase tracking-wide">{label}</div>
  </GlassCard>
);

// ─── Main Component ──────────────────────────────────────────────────────────

const ProfileTab: React.FC = () => {
  const [data, setData] = useState<ProfileSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    profileSummaryProfileSummaryGet()
      .then((res) => setData(res.data ?? null))
      .catch((err) => setError(err?.message ?? 'Failed to load profile'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Loader2 className="animate-spin h-8 w-8 text-wine-rose" strokeWidth={1.5} />
        <p className="text-white/60 text-sm">Building your palate profile…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-wine-burgundy/30 border border-wine-rose/40 text-white/90 px-4 py-3 rounded-xl">
        <strong className="font-bold">Error: </strong>{error}
      </div>
    );
  }

  if (!data) return null;

  const markers = data.tasteMarkers as TasteMarkers | null | undefined;
  const stats = data.cellarStats;

  const vintageRange =
    stats?.vintageOldest && stats?.vintageNewest
      ? `${stats.vintageOldest} – ${stats.vintageNewest}`
      : '—';

  return (
    <div className="space-y-6">

      {/* ── Palate Portrait ─────────────────────────────────────────────── */}
      <GlassCard className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <BookOpen className="h-5 w-5 text-wine-gold" strokeWidth={1.5} />
          <h2 className="text-lg font-semibold text-white">Palate Portrait</h2>
        </div>
        {data.styleSummary ? (
          <p className="text-white/80 italic leading-relaxed">"{data.styleSummary}"</p>
        ) : (
          <p className="text-white/40 text-sm italic">
            Run a recommendation to generate your personalised palate portrait.
          </p>
        )}
      </GlassCard>

      {/* ── Cellar at a Glance ──────────────────────────────────────────── */}
      {stats && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <LayoutGrid className="h-4 w-4 text-white/50" strokeWidth={1.5} />
            <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wide">Cellar at a Glance</h2>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <StatCard label="Total Bottles" value={stats.totalBottles ?? 0} />
            <StatCard label="Unique Wines" value={stats.uniqueWines ?? 0} />
            <StatCard label="Vintage Range" value={vintageRange} />
          </div>
        </div>
      )}

      {/* ── Taste Profile Markers ────────────────────────────────────────── */}
      {markers && (
        <GlassCard className="p-6">
          <div className="flex items-center gap-2 mb-5">
            <Sparkles className="h-5 w-5 text-wine-gold" strokeWidth={1.5} />
            <h2 className="text-lg font-semibold text-white">Taste Profile</h2>
          </div>
          <div className="space-y-4">
            <MarkerBar label="Acidity" value={markers.acidity} />
            <MarkerBar label="Tannin"  value={markers.tannin}  />
            <MarkerBar label="Body"    value={markers.body}    />
            <MarkerBar label="Oak"     value={markers.oak}     />
          </div>
          <p className="text-xs text-white/30 mt-4">
            Derived from your tasting note descriptors — indicative, not prescriptive.
          </p>
        </GlassCard>
      )}

      {/* ── Flavour Preferences ─────────────────────────────────────────── */}
      {data.preferredDescriptors && data.preferredDescriptors.length > 0 && (
        <GlassCard className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Wine className="h-5 w-5 text-wine-gold" strokeWidth={1.5} />
            <h2 className="text-lg font-semibold text-white">Flavour Preferences</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.preferredDescriptors.map((d, i) => (
              <span
                key={i}
                className="px-3 py-1 rounded-full text-sm border border-wine-gold/40 text-wine-gold bg-wine-gold/10"
              >
                {d}
              </span>
            ))}
          </div>
        </GlassCard>
      )}

      {/* ── Styles to Avoid ──────────────────────────────────────────────── */}
      {data.avoidedStyles && data.avoidedStyles.length > 0 && (
        <GlassCard className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <ThumbsDown className="h-5 w-5 text-wine-rose" strokeWidth={1.5} />
            <h2 className="text-lg font-semibold text-white">Styles to Avoid</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.avoidedStyles.map((s, i) => (
              <span
                key={i}
                className="px-3 py-1 rounded-full text-sm border border-wine-rose/40 text-wine-rose bg-wine-rose/10"
              >
                {s}
              </span>
            ))}
          </div>
        </GlassCard>
      )}

      {/* ── Top Varietals & Regions ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {data.topVarietals && data.topVarietals.length > 0 && (
          <GlassCard className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Wine className="h-4 w-4 text-white/50" strokeWidth={1.5} />
              <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wide">Top Varietals</h2>
            </div>
            <ol className="space-y-2">
              {data.topVarietals.map((v, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="w-5 h-5 flex items-center justify-center rounded-full bg-wine-gold/20 text-wine-gold text-xs font-bold shrink-0">
                    {i + 1}
                  </span>
                  <span className="text-sm text-white/80">{v}</span>
                </li>
              ))}
            </ol>
          </GlassCard>
        )}

        {data.topRegions && data.topRegions.length > 0 && (
          <GlassCard className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <MapPin className="h-4 w-4 text-white/50" strokeWidth={1.5} />
              <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wide">Top Regions</h2>
            </div>
            <ol className="space-y-2">
              {data.topRegions.map((r, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="w-5 h-5 flex items-center justify-center rounded-full bg-wine-rose/20 text-wine-rose text-xs font-bold shrink-0">
                    {i + 1}
                  </span>
                  <span className="text-sm text-white/80">{r}</span>
                </li>
              ))}
            </ol>
          </GlassCard>
        )}

      </div>

      {/* ── Average Spend ────────────────────────────────────────────────── */}
      {data.avgSpend != null && (
        <GlassCard className="p-6">
          <p className="text-sm text-white/60 mb-1">Average Bottle Spend</p>
          <p className="text-3xl font-bold text-white">${data.avgSpend}</p>
        </GlassCard>
      )}

    </div>
  );
};

export default ProfileTab;
