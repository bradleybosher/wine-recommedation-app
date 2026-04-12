import React, { useState } from 'react';
import FileUploader from './FileUploader';
import { uploadProfileUploadProfilePost } from './client';
import type { UploadProfileResponse } from './client/types.gen';
import GlassCard from '@/components/ui/GlassCard';
import { CheckCircle2, Loader2 } from 'lucide-react';

interface UploadTastingHistoryScreenProps {
  onSuccess: (response: UploadProfileResponse) => void;
  onSkip: () => void;
}

const UploadTastingHistoryScreen: React.FC<UploadTastingHistoryScreenProps> = ({ onSuccess, onSkip }) => {
  const [fileData, setFileData] = useState({
    file: null as File | null,
    previewUrl: '',
    base64: ''
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<UploadProfileResponse | null>(null);

  const handleFileChange = (file: File | null, previewUrl: string, base64: string, errorMsg: string) => {
    setFileData({ file, previewUrl, base64 });
    if (errorMsg) {
      setError(errorMsg);
    } else if (error) {
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileData.file) return;

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await uploadProfileUploadProfilePost({
        body: {
          file: fileData.file
        }
      });

      if (response && response.data) {
        setResult(response.data);
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err: any) {
      const errorMsg = err instanceof Error ? err.message : err.data?.detail || 'Failed to upload profile';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  if (result) {
    const profile = result.tasteProfile;
    const hasProfileData = profile && (
      (profile.preferredGrapes?.length ?? 0) > 0 ||
      (profile.preferredRegions?.length ?? 0) > 0 ||
      (profile.preferredStyles?.length ?? 0) > 0 ||
      (profile.avoidedStyles?.length ?? 0) > 0 ||
      profile.budgetMin != null
    );

    return (
      <GlassCard className="p-8">
        <div className="text-center mb-6">
          <CheckCircle2 className="mx-auto h-12 w-12 text-wine-gold mb-4" strokeWidth={1.5} />
          <h2 className="text-2xl font-bold text-white mb-1">Taste Profile Refined</h2>
          <p className="text-white/60 text-sm">{result.message}</p>
        </div>

        {hasProfileData ? (
          <div className="space-y-4 mb-6">
            <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wide">Inferred Preferences</h3>

            {profile.preferredGrapes && profile.preferredGrapes.length > 0 && (
              <div className="bg-white/5 p-4 rounded-xl">
                <p className="text-xs font-medium text-white/50 mb-2">Grapes</p>
                <div className="flex flex-wrap gap-2">
                  {profile.preferredGrapes.map((grape, i) => (
                    <span key={i} className="px-3 py-1 bg-wine-purple-mid/40 text-white border border-white/20 text-sm font-medium rounded-full capitalize">
                      {grape}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {profile.preferredRegions && profile.preferredRegions.length > 0 && (
              <div className="bg-white/5 p-4 rounded-xl">
                <p className="text-xs font-medium text-white/50 mb-2">Regions</p>
                <div className="flex flex-wrap gap-2">
                  {profile.preferredRegions.map((region, i) => (
                    <span key={i} className="px-3 py-1 bg-wine-amber/20 text-wine-gold border border-wine-amber/30 text-sm font-medium rounded-full capitalize">
                      {region}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {profile.preferredStyles && profile.preferredStyles.length > 0 && (
              <div className="bg-white/5 p-4 rounded-xl">
                <p className="text-xs font-medium text-white/50 mb-2">Style Descriptors</p>
                <div className="flex flex-wrap gap-2">
                  {profile.preferredStyles.map((style, i) => (
                    <span key={i} className="px-3 py-1 bg-wine-merlot/30 text-white border border-wine-rose/30 text-sm font-medium rounded-full capitalize">
                      {style}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {profile.avoidedStyles && profile.avoidedStyles.length > 0 && (
              <div className="bg-wine-burgundy/15 p-4 rounded-xl border border-wine-rose/30">
                <p className="text-xs font-medium text-wine-rose mb-2">Avoided Styles</p>
                <div className="flex flex-wrap gap-2">
                  {profile.avoidedStyles.map((style, i) => (
                    <span key={i} className="px-3 py-1 bg-wine-burgundy/40 text-wine-rose border border-wine-rose/40 text-sm font-medium rounded-full capitalize">
                      {style}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {profile.budgetMin != null && profile.budgetMax != null && (
              <div className="bg-white/5 p-4 rounded-xl">
                <p className="text-xs font-medium text-white/50 mb-1">Typical Spend</p>
                <p className="text-lg font-semibold text-white">${profile.budgetMin} – ${profile.budgetMax} per bottle</p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-wine-amber/10 border border-wine-amber/30 rounded-xl p-4 mb-6">
            <p className="text-sm text-wine-gold">
              Profile saved, but not enough tasting data to infer preferences yet. Add more exports (notes, consumed) to improve recommendations.
            </p>
          </div>
        )}

        <button
          onClick={() => onSuccess(result)}
          className="w-full flex justify-center py-3 px-4 border border-wine-rose/30 rounded-md shadow-sm text-lg font-medium text-white bg-wine-burgundy hover:bg-wine-merlot focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-wine-rose transition-colors shadow-[0_0_20px_rgba(139,37,70,0.4)]"
        >
          Continue
        </button>
      </GlassCard>
    );
  }

  return (
    <GlassCard className="p-8">
      <h2 className="text-2xl font-bold text-white mb-2">Step 2: Refine Your Taste Profile</h2>
      <p className="text-white/70 mb-6">
        Upload tasting notes or a separate CellarTracker export to refine your taste profile. (Optional—use the same file again, or skip to proceed)
      </p>

      {error && (
        <div className="bg-wine-burgundy/30 border border-wine-rose/40 text-white/90 px-4 py-3 rounded-xl mb-6">
          <strong className="font-bold">Error: </strong>
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <FileUploader
          onFileChange={handleFileChange}
          file={fileData.file}
          previewUrl={fileData.previewUrl}
          error={error}
        />

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={!fileData.file || isLoading}
            className={`flex-1 flex justify-center py-3 px-4 border rounded-md shadow-sm text-lg font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors ${
              !fileData.file || isLoading
                ? 'bg-white/10 text-white/30 cursor-not-allowed border-white/10'
                : 'bg-wine-burgundy hover:bg-wine-merlot border-wine-rose/30 focus:ring-wine-rose shadow-[0_0_20px_rgba(139,37,70,0.4)]'
            }`}
          >
            {isLoading ? (
              <div className="flex items-center">
                <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" strokeWidth={1.5} />
                Uploading profile...
              </div>
            ) : (
              'Upload Tasting History'
            )}
          </button>

          <button
            type="button"
            onClick={onSkip}
            className="flex-1 flex justify-center py-3 px-4 border border-white/20 rounded-md shadow-sm text-lg font-medium text-white/70 hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-wine-rose transition-colors"
          >
            Skip for Now
          </button>
        </div>
      </form>
    </GlassCard>
  );
};

export default UploadTastingHistoryScreen;
