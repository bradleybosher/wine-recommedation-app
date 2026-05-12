import React, { useState } from 'react';
import UploadCellarInventoryScreen from './UploadCellarInventoryScreen';
import UploadTastingHistoryScreen from './UploadTastingHistoryScreen';
import SeedBottlesScreen from './SeedBottlesScreen';
import type { UploadInventoryResponse, UploadProfileResponse } from './client/types.gen';
import GlassCard from '@/components/ui/GlassCard';
import { CheckCircle2, FileSpreadsheet, Wine } from 'lucide-react';

interface UploadFlowProps {
  onComplete: () => void;
}

type Pathway = 'choose' | 'cellartracker' | 'seed';
type CtStep = 'inventory' | 'profile' | 'complete';

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
      <div className="min-h-screen flex items-center justify-center p-4">
        <GlassCard className="p-8 max-w-md text-center">
          <CheckCircle2 className="h-20 w-20 text-wine-gold mx-auto mb-6" strokeWidth={1.5} />

          <h1 className="text-3xl font-bold text-white mb-4">Your Taste Profile is Ready!</h1>
          <p className="text-white/70 mb-6">
            {isSeed
              ? "Your palate has been inferred from the wines you named. Now upload a restaurant wine list to get personalized recommendations."
              : "Your taste profile has been established from your cellar. Now upload a restaurant wine list to get personalized recommendations."}
          </p>

          <div className="space-y-3 mb-8">
            {inventoryResult && (
              <div className="flex items-center justify-center gap-2 text-wine-gold">
                <CheckCircle2 className="h-5 w-5" strokeWidth={1.5} />
                <span>{inventoryResult.count} wines analyzed</span>
              </div>
            )}
            {profileResult && (
              <div className="flex items-center justify-center gap-2 text-wine-gold">
                <CheckCircle2 className="h-5 w-5" strokeWidth={1.5} />
                <span>Taste profile refined</span>
              </div>
            )}
            {seedResult && (
              <div className="flex items-center justify-center gap-2 text-wine-gold">
                <CheckCircle2 className="h-5 w-5" strokeWidth={1.5} />
                <span>Profile inferred · {conf} confidence</span>
              </div>
            )}
            {!profileResult && !seedResult && (
              <div className="flex items-center justify-center gap-2 text-white/80">
                <CheckCircle2 className="h-5 w-5" strokeWidth={1.5} />
                <span>Ready to analyze restaurant wine lists</span>
              </div>
            )}
          </div>

          <button
            onClick={onComplete}
            className="w-full bg-wine-burgundy hover:bg-wine-merlot text-white font-bold py-3 px-4 rounded-lg border border-wine-rose/30 transition-colors shadow-[0_0_20px_rgba(139,37,70,0.4)]"
          >
            Analyze a Wine List
          </button>
        </GlassCard>
      </div>
    );
  }

  if (pathway === 'choose') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-3xl w-full">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">How would you like to start?</h1>
            <p className="text-white/70">Pick the pathway that fits how much data you can share.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <button
              onClick={() => setPathway('cellartracker')}
              className="text-left"
            >
              <GlassCard className="p-6 h-full hover:bg-white/10 transition-colors border border-white/10 hover:border-wine-rose/40">
                <FileSpreadsheet className="h-10 w-10 text-wine-gold mb-4" strokeWidth={1.5} />
                <h2 className="text-xl font-bold text-white mb-2">I use CellarTracker</h2>
                <p className="text-white/70 text-sm mb-3">
                  Upload your cellar inventory and tasting history TSV exports. Highest-fidelity
                  profile, grounded in your actual ratings.
                </p>
                <p className="text-xs text-wine-gold uppercase tracking-wide">High confidence</p>
              </GlassCard>
            </button>
            <button
              onClick={() => setPathway('seed')}
              className="text-left"
            >
              <GlassCard className="p-6 h-full hover:bg-white/10 transition-colors border border-white/10 hover:border-wine-rose/40">
                <Wine className="h-10 w-10 text-wine-rose mb-4" strokeWidth={1.5} />
                <h2 className="text-xl font-bold text-white mb-2">Name a few wines I love</h2>
                <p className="text-white/70 text-sm mb-3">
                  Tell us 3–7 wines you have loved (and a few you disliked). We'll infer your palate
                  in 60 seconds — no exports required.
                </p>
                <p className="text-xs text-wine-rose uppercase tracking-wide">Medium confidence</p>
              </GlassCard>
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (pathway === 'seed') {
    return (
      <div className="min-h-screen py-12 px-4">
        <div className="max-w-2xl mx-auto">
          <SeedBottlesScreen
            onSuccess={handleSeedSuccess}
            onBack={() => setPathway('choose')}
          />
        </div>
      </div>
    );
  }

  // CellarTracker pathway
  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <div className="flex justify-between mb-4">
            <div className={`flex-1 text-center ${ctStep === 'inventory' || (ctStep === 'profile' && !!inventoryResult) ? 'text-wine-rose' : 'text-white/40'}`}>
              <div className={`inline-flex items-center justify-center h-8 w-8 rounded-full font-bold ${ctStep === 'inventory' || (ctStep === 'profile' && !!inventoryResult) ? 'bg-wine-burgundy text-white border border-wine-rose/40' : 'bg-white/10 text-white/50 border border-white/20'}`}>
                {inventoryResult ? <CheckCircle2 className="h-4 w-4" strokeWidth={2} /> : '1'}
              </div>
              <p className="text-sm font-medium mt-2">Cellar</p>
            </div>

            <div className="flex-1 text-center relative">
              <div className={`absolute top-4 left-0 right-0 h-0.5 ${inventoryResult ? 'bg-wine-rose/60' : 'bg-white/20'}`}></div>
              <div className={`inline-flex items-center justify-center h-8 w-8 rounded-full font-bold relative z-10 ${ctStep === 'profile' ? 'bg-wine-burgundy text-white border border-wine-rose/40' : 'bg-white/10 text-white/50 border border-white/20'}`}>
                {profileResult ? <CheckCircle2 className="h-4 w-4" strokeWidth={2} /> : '2'}
              </div>
              <p className="text-sm font-medium mt-2">Refine</p>
            </div>

            <div className="flex-1 text-center">
              <div className="inline-flex items-center justify-center h-8 w-8 rounded-full font-bold bg-white/10 text-white/50 border border-white/20">
                3
              </div>
              <p className="text-sm font-medium mt-2">Analyze</p>
            </div>
          </div>
          <button
            onClick={() => setPathway('choose')}
            className="text-sm text-white/60 hover:text-white underline"
          >
            ← Change pathway
          </button>
        </div>

        {ctStep === 'inventory' && (
          <UploadCellarInventoryScreen
            onSuccess={handleInventorySuccess}
            onSkip={handleInventorySkip}
          />
        )}

        {ctStep === 'profile' && (
          <UploadTastingHistoryScreen onSuccess={handleProfileSuccess} onSkip={handleProfileSkip} />
        )}
      </div>
    </div>
  );
};

export default UploadFlow;
