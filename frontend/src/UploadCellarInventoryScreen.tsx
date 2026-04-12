import React, { useState } from 'react';
import FileUploader from './FileUploader';
import { uploadInventoryUploadInventoryPost, getInventoryInventoryGet } from './client';
import type { UploadInventoryResponse, InventoryResponse } from './client/types.gen';
import GlassCard from '@/components/ui/GlassCard';
import { CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';

interface UploadCellarInventoryScreenProps {
  onSuccess: (response: UploadInventoryResponse) => void;
}

const UploadCellarInventoryScreen: React.FC<UploadCellarInventoryScreenProps> = ({ onSuccess }) => {
  const [fileData, setFileData] = useState({
    file: null as File | null,
    previewUrl: '',
    base64: ''
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<UploadInventoryResponse | null>(null);
  const [inventoryDetails, setInventoryDetails] = useState<InventoryResponse | null>(null);

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
    setInventoryDetails(null);

    try {
      const response = await uploadInventoryUploadInventoryPost({
        body: {
          file: fileData.file
        }
      });

      if (response && response.data) {
        setResult(response.data);

        // Fetch inventory details to get staleness info
        try {
          const inventoryResponse = await getInventoryInventoryGet();
          if (inventoryResponse && inventoryResponse.data) {
            setInventoryDetails(inventoryResponse.data);
          }
        } catch (inventoryErr) {
          console.log('Could not fetch inventory details');
        }

        // Notify parent of success
        onSuccess(response.data);
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err: any) {
      const errorMsg = err instanceof Error ? err.message : err.data?.detail || 'Failed to upload inventory';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  if (result) {
    const stale = inventoryDetails?.stale;
    const ageHours = inventoryDetails?.ageHours;

    const getAgeDescription = (hours: number | null | undefined): string => {
      if (!hours) return 'recently exported';
      if (hours < 1) return 'just now';
      if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
      const days = Math.floor(hours / 24);
      return `${days} day${days !== 1 ? 's' : ''} ago`;
    };

    return (
      <GlassCard className="p-8">
        <div className="text-center">
          <CheckCircle2 className="mx-auto h-12 w-12 text-wine-gold mb-4" strokeWidth={1.5} />
          <h2 className="text-2xl font-bold text-white mb-2">Cellar Inventory Loaded</h2>
          <p className="text-white/70 mb-6">{result.message}</p>
          <div className="bg-white/5 border border-white/15 rounded-lg p-4 mb-6">
            <p className="text-lg font-semibold text-white">
              {result.count} {result.count === 1 ? 'bottle' : 'bottles'} found
            </p>
            {ageHours !== null && ageHours !== undefined && (
              <p className="text-sm text-white/70 mt-2">
                Export from {getAgeDescription(ageHours)}
              </p>
            )}
          </div>

          {stale && (
            <div className="bg-wine-amber/15 border border-wine-amber/40 rounded-lg p-4 text-left">
              <div className="flex gap-3">
                <AlertTriangle className="h-5 w-5 text-wine-amber flex-shrink-0 mt-0.5" strokeWidth={1.5} />
                <div>
                  <p className="font-semibold text-white">Your inventory may be outdated</p>
                  <p className="text-sm text-white/80 mt-1">
                    This export is older than a few weeks. Consider uploading a fresh CellarTracker export for more accurate recommendations.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard className="p-8">
      <h2 className="text-2xl font-bold text-white mb-2">Step 1: Your Cellar Inventory</h2>
      <p className="text-white/70 mb-6">
        Upload a CellarTracker export (TSV file) of your wine collection. We'll analyze your cellar to understand your taste preferences.
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

        <button
          type="submit"
          disabled={!fileData.file || isLoading}
          className={`w-full flex justify-center py-3 px-4 border rounded-md shadow-sm text-lg font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors ${
            !fileData.file || isLoading
              ? 'bg-white/10 text-white/30 cursor-not-allowed border-white/10'
              : 'bg-wine-burgundy hover:bg-wine-merlot border-wine-rose/30 focus:ring-wine-rose shadow-[0_0_20px_rgba(139,37,70,0.4)]'
          }`}
        >
          {isLoading ? (
            <div className="flex items-center">
              <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" strokeWidth={1.5} />
              Uploading inventory...
            </div>
          ) : (
            'Upload & Continue'
          )}
        </button>
      </form>
    </GlassCard>
  );
};

export default UploadCellarInventoryScreen;
