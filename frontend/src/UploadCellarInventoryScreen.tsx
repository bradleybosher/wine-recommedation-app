import React, { useState } from 'react';
import FileUploader from './FileUploader';
import { uploadInventoryUploadInventoryPost, getInventoryInventoryGet } from './client';
import type { UploadInventoryResponse, InventoryResponse } from './client/types.gen';
import { INK, INK_SOFT, OXBLOOD, PAPER, RULE } from '@/design/tokens';
import { Loader2 } from 'lucide-react';

interface UploadCellarInventoryScreenProps {
  onSuccess: (response: UploadInventoryResponse) => void;
  onSkip?: () => void;
}

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

const skipBtn: React.CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: 12,
  letterSpacing: 2,
  textTransform: 'uppercase',
  padding: '10px 18px',
  background: 'transparent',
  color: INK_SOFT,
  border: `1px solid ${RULE}`,
  cursor: 'pointer',
};

const UploadCellarInventoryScreen: React.FC<UploadCellarInventoryScreenProps> = ({ onSuccess, onSkip }) => {
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
        body: { file: fileData.file }
      });

      if (response && response.data) {
        setResult(response.data);

        try {
          const inventoryResponse = await getInventoryInventoryGet();
          if (inventoryResponse && inventoryResponse.data) {
            setInventoryDetails(inventoryResponse.data);
          }
        } catch {
          // non-fatal
        }

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
          Cellar Inventory Loaded
        </div>
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: 28,
            color: INK,
            letterSpacing: -0.3,
            marginBottom: 4,
          }}
        >
          {result.count} {result.count === 1 ? 'bottle' : 'bottles'} on record
        </div>
        {ageHours != null && (
          <div
            style={{
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: 13,
              color: INK_SOFT,
              marginBottom: 16,
            }}
          >
            Export from {getAgeDescription(ageHours)}
          </div>
        )}
        {stale && (
          <div
            style={{
              borderTop: `1px solid ${RULE}`,
              paddingTop: 12,
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: 13,
              color: INK_SOFT,
            }}
          >
            This export is older than a few weeks. Consider uploading a fresh CellarTracker
            export for more accurate recommendations.
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          borderTop: `2px solid ${INK}`,
          borderBottom: `1px solid ${RULE}`,
          padding: '16px 0',
          marginBottom: 20,
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
            marginBottom: 4,
          }}
        >
          Step 1 · Cellar Inventory
        </div>
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: 14,
            color: INK_SOFT,
          }}
        >
          Upload a CellarTracker export (TSV file) of your wine collection.
        </div>
      </div>

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

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <FileUploader
          onFileChange={handleFileChange}
          file={fileData.file}
          previewUrl={fileData.previewUrl}
          error={error}
        />

        <div style={{ display: 'flex', gap: 12 }}>
          <button
            type="submit"
            disabled={!fileData.file || isLoading}
            style={submitBtn(!!fileData.file && !isLoading)}
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" style={{ width: 16, height: 16 }} strokeWidth={1.5} />
                Uploading inventory…
              </>
            ) : (
              'Upload & Continue'
            )}
          </button>

          {onSkip && (
            <button type="button" onClick={onSkip} style={skipBtn}>
              Skip
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default UploadCellarInventoryScreen;
