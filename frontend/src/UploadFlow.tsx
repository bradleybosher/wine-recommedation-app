import React, { useState } from 'react';
import UploadCellarInventoryScreen from './UploadCellarInventoryScreen';
import UploadTastingHistoryScreen from './UploadTastingHistoryScreen';
import type { UploadInventoryResponse, UploadProfileResponse } from './client/types.gen';
import GlassCard from '@/components/ui/GlassCard';
import { CheckCircle2 } from 'lucide-react';

interface UploadFlowProps {
  onComplete: () => void;
}

type Step = 'inventory' | 'profile' | 'complete';

const UploadFlow: React.FC<UploadFlowProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState<Step>('inventory');
  const [inventoryResult, setInventoryResult] = useState<UploadInventoryResponse | null>(null);
  const [profileResult, setProfileResult] = useState<UploadProfileResponse | null>(null);

  const handleInventorySuccess = (result: UploadInventoryResponse) => {
    setInventoryResult(result);
    // Auto-advance to profile step after a short delay
    setTimeout(() => {
      setCurrentStep('profile');
    }, 1500);
  };

  const handleProfileSuccess = (result: UploadProfileResponse) => {
    setProfileResult(result);
    // Auto-advance to complete step
    setTimeout(() => {
      setCurrentStep('complete');
    }, 1500);
  };

  const handleProfileSkip = () => {
    setCurrentStep('complete');
  };

  if (currentStep === 'complete') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <GlassCard className="p-8 max-w-md text-center">
          <CheckCircle2 className="h-20 w-20 text-wine-gold mx-auto mb-6" strokeWidth={1.5} />

          <h1 className="text-3xl font-bold text-white mb-4">Your Taste Profile is Ready!</h1>
          <p className="text-white/70 mb-6">
            Your taste profile has been established from your cellar. Now upload a restaurant wine list to get personalized recommendations.
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
            {!profileResult && (
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

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Progress indicator */}
        <div className="mb-8">
          <div className="flex justify-between mb-4">
            <div className={`flex-1 text-center ${currentStep === 'inventory' || (currentStep === 'profile' && !!inventoryResult) ? 'text-wine-rose' : 'text-white/40'}`}>
              <div className={`inline-flex items-center justify-center h-8 w-8 rounded-full font-bold ${currentStep === 'inventory' || (currentStep === 'profile' && !!inventoryResult) ? 'bg-wine-burgundy text-white border border-wine-rose/40' : 'bg-white/10 text-white/50 border border-white/20'}`}>
                {inventoryResult ? <CheckCircle2 className="h-4 w-4" strokeWidth={2} /> : '1'}
              </div>
              <p className="text-sm font-medium mt-2">Cellar</p>
            </div>

            <div className="flex-1 text-center relative">
              <div className={`absolute top-4 left-0 right-0 h-0.5 ${inventoryResult ? 'bg-wine-rose/60' : 'bg-white/20'}`}></div>
              <div className={`inline-flex items-center justify-center h-8 w-8 rounded-full font-bold relative z-10 ${currentStep === 'profile' ? 'bg-wine-burgundy text-white border border-wine-rose/40' : 'bg-white/10 text-white/50 border border-white/20'}`}>
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
        </div>

        {/* Content */}
        {currentStep === 'inventory' && (
          <UploadCellarInventoryScreen onSuccess={handleInventorySuccess} />
        )}

        {currentStep === 'profile' && (
          <UploadTastingHistoryScreen onSuccess={handleProfileSuccess} onSkip={handleProfileSkip} />
        )}
      </div>
    </div>
  );
};

export default UploadFlow;
