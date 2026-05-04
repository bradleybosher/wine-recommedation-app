import React, { useState } from 'react';
import type { RecommendationResponse, WineRecommendation } from '@/client/types.gen';
import GlassCard from '@/components/ui/GlassCard';
import WineBottleIcon, { getWineStyle } from '@/components/ui/WineBottleIcon';
import { Copy, Check, Loader2, Sparkles } from 'lucide-react';

const RERANK_CHIPS: { label: string; terms: string }[] = [
  { label: 'Under $80', terms: 'budget under $80, value-focused' },
  { label: 'More adventurous', terms: 'natural, funky, off-beat, lesser-known producers' },
  { label: 'Food match first', terms: 'pairing-led, classic match for the meal' },
  { label: 'Safer crowd-pleaser', terms: 'crowd-pleasing, approachable, classic style' },
];

interface RecommendationResultsProps {
  response: RecommendationResponse;
  onNewSearch: () => void;
  onRerank?: (terms: string) => void;
  isRerankLoading?: boolean;
}

const RecommendationResults: React.FC<RecommendationResultsProps> = ({
  response,
  onNewSearch,
  onRerank,
  isRerankLoading = false,
}) => {
  const [activeChip, setActiveChip] = useState<string | null>(null);

  const handleChipClick = (label: string, terms: string) => {
    if (!onRerank || isRerankLoading) return;
    setActiveChip(label);
    onRerank(terms);
  };

  const getConfidenceBadgeColor = (confidence: string): string => {
    const level = confidence.split(/[\s—–-]/)[0].toLowerCase();
    switch (level) {
      case 'high':
        return 'bg-wine-amber/20 text-wine-gold border-wine-amber/40';
      case 'medium':
        return 'bg-wine-rose/15 text-wine-rose border-wine-rose/30';
      case 'low':
        return 'bg-white/10 text-white/60 border-white/20';
      default:
        return 'bg-white/10 text-white/50 border-white/15';
    }
  };

  const handleCopyClick = async (recommendation: WineRecommendation) => {
    const text = `${recommendation.wineName}${recommendation.producer ? ` by ${recommendation.producer}` : ''}${
      recommendation.vintage ? ` (${recommendation.vintage})` : ''
    }${recommendation.price ? ` - $${recommendation.price}` : ''}`;

    try {
      await navigator.clipboard.writeText(text);
      alert('Copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="mt-10">
      <h2 className="text-2xl font-bold text-white mb-6">Your Wine Recommendations</h2>

      {response.profileMatchSummary && (
        <div className="bg-wine-purple-mid/20 border border-wine-rose/25 text-white/90 p-4 rounded-xl mb-6">
          <h3 className="font-semibold mb-2">Match Summary</h3>
          <p>{response.profileMatchSummary}</p>
        </div>
      )}

      {response.listQualityNote && (
        <div className="bg-wine-amber/15 border border-wine-amber/30 text-white/90 p-3 rounded-xl mb-6 text-sm">
          <span className="font-medium">Note on list quality:</span> {response.listQualityNote}
        </div>
      )}

      {onRerank && (
        <div className="flex flex-wrap items-center gap-2 mb-6">
          <span className="inline-flex items-center text-xs uppercase tracking-wide text-white/60 mr-1">
            <Sparkles className="w-3.5 h-3.5 mr-1.5 text-wine-gold" strokeWidth={1.5} />
            Refine
          </span>
          {RERANK_CHIPS.map((chip) => {
            const isActive = activeChip === chip.label;
            return (
              <button
                key={chip.label}
                type="button"
                onClick={() => handleChipClick(chip.label, chip.terms)}
                disabled={isRerankLoading}
                className={`inline-flex items-center rounded-full px-3 py-1 text-sm border transition-colors focus:outline-none focus:ring-2 focus:ring-wine-rose ${
                  isActive
                    ? 'bg-wine-burgundy/40 border-wine-rose/40 text-white'
                    : 'border-glass-border text-white/80 hover:bg-glass-surface-hover'
                } ${isRerankLoading ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                {isActive && isRerankLoading && (
                  <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" strokeWidth={1.5} />
                )}
                {chip.label}
              </button>
            );
          })}
        </div>
      )}

      {response.recommendations.length > 0 ? (
        <div className={`space-y-6 transition-opacity ${isRerankLoading ? 'opacity-50' : ''}`}>
          {response.recommendations.map((rec) => (
            <GlassCard key={rec.rank} className="p-6 hover:bg-glass-surface-hover transition-colors">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-wine-burgundy text-white font-bold text-sm border border-wine-rose/40">
                    {rec.rank}
                  </span>
                  <WineBottleIcon style={getWineStyle(rec.wineName, rec.region)} />
                  <div>
                    <h3 className="text-xl font-semibold text-white">{rec.wineName}</h3>
                    {rec.producer && (
                      <p className="text-sm text-white/70">{rec.producer}</p>
                    )}
                  </div>
                </div>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium border ${getConfidenceBadgeColor(rec.confidence)}`}>
                  {rec.confidence}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                {rec.vintage && (
                  <div className="bg-white/5 border border-white/10 p-3 rounded-lg">
                    <div className="text-xs font-medium text-white/50 uppercase">Vintage</div>
                    <div className="text-lg font-semibold text-white">{rec.vintage}</div>
                  </div>
                )}
                {rec.region && (
                  <div className="bg-white/5 border border-white/10 p-3 rounded-lg">
                    <div className="text-xs font-medium text-white/50 uppercase">Region</div>
                    <div className="text-sm font-semibold text-white">{rec.region}</div>
                  </div>
                )}
                {rec.price && (
                  <div className="bg-white/5 border border-white/10 p-3 rounded-lg">
                    <div className="text-xs font-medium text-white/50 uppercase">Price</div>
                    <div className="text-lg font-semibold text-white">${rec.price}</div>
                  </div>
                )}
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-semibold text-white/80 mb-2">Why this wine?</h4>
                <p className="text-white/80 leading-relaxed">{rec.reasoning}</p>
              </div>

              {rec.fitMarkers && rec.fitMarkers.length > 0 && (
                <div className="mb-4 pt-3 border-t border-white/10">
                  <h5 className="text-xs uppercase tracking-wide text-white/60 mb-2">
                    Why this fits you
                  </h5>
                  <ul className="space-y-1">
                    {rec.fitMarkers.map((marker, idx) => (
                      <li key={idx} className="text-sm text-white/80 flex items-start gap-2">
                        <Check className="w-3.5 h-3.5 mt-0.5 text-wine-gold shrink-0" strokeWidth={1.5} />
                        <span>{marker}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <button
                onClick={() => handleCopyClick(rec)}
                className="inline-flex items-center text-sm text-white/50 hover:text-white/90 font-medium focus:outline-none focus:ring-2 focus:ring-wine-rose focus:ring-offset-2 rounded px-2 py-1 transition-colors"
              >
                <Copy className="h-4 w-4 mr-1.5" strokeWidth={1.5} />
                Copy to clipboard
              </button>
            </GlassCard>
          ))}
        </div>
      ) : (
        <p className="text-white/70 text-center py-8">No recommendations found for this wine list.</p>
      )}

      <div className="mt-8 text-center">
        <button
          onClick={onNewSearch}
          className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white/80 font-medium rounded-md border border-white/20 focus:outline-none focus:ring-2 focus:ring-wine-rose transition-colors"
        >
          Search Another Wine List
        </button>
      </div>
    </div>
  );
};

export default RecommendationResults;
