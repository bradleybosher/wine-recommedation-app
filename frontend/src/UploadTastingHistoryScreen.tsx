import React, { useState } from 'react';
import FileUploader from './FileUploader';
import { uploadProfileUploadProfilePost } from './client';
import type { UploadProfileResponse } from './client/types.gen';
import { INK, INK_SOFT, OXBLOOD, PAPER, RULE, space, typeScale } from '@/design/tokens';
import { Loader2 } from 'lucide-react';

interface UploadTastingHistoryScreenProps {
  onSuccess: (response: UploadProfileResponse) => void;
  onSkip: () => void;
}

const submitBtn = (enabled: boolean): React.CSSProperties => ({
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: typeScale.bodyLg,
  letterSpacing: 3,
  textTransform: 'uppercase',
  padding: `${space.sm} ${space.md}`,
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
  fontSize: typeScale.label,
  letterSpacing: 2,
  textTransform: 'uppercase',
  padding: `${space.sm} ${space.md}`,
  background: 'transparent',
  color: INK_SOFT,
  border: `1px solid ${RULE}`,
  cursor: 'pointer',
};

const tagStyle: React.CSSProperties = {
  fontFamily: "'EB Garamond', serif",
  fontSize: typeScale.label,
  padding: '2px 8px',
  border: `1px solid ${RULE}`,
  color: INK_SOFT,
};

const sectionLabel: React.CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: typeScale.micro,
  letterSpacing: 2,
  textTransform: 'uppercase',
  color: INK_SOFT,
  marginBottom: 6,
};

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
        body: { file: fileData.file }
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
            fontSize: typeScale.micro,
            letterSpacing: 3,
            textTransform: 'uppercase',
            color: OXBLOOD,
            marginBottom: 12,
          }}
        >
          Taste Profile Refined
        </div>

        {hasProfileData ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 20 }}>
            {profile.preferredGrapes && profile.preferredGrapes.length > 0 && (
              <div>
                <div style={sectionLabel}>Grapes</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {profile.preferredGrapes.map((grape, i) => (
                    <span key={i} style={tagStyle}>{grape}</span>
                  ))}
                </div>
              </div>
            )}

            {profile.preferredRegions && profile.preferredRegions.length > 0 && (
              <div>
                <div style={sectionLabel}>Regions</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {profile.preferredRegions.map((region, i) => (
                    <span key={i} style={tagStyle}>{region}</span>
                  ))}
                </div>
              </div>
            )}

            {profile.preferredStyles && profile.preferredStyles.length > 0 && (
              <div>
                <div style={sectionLabel}>Style</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {profile.preferredStyles.map((style, i) => (
                    <span key={i} style={tagStyle}>{style}</span>
                  ))}
                </div>
              </div>
            )}

            {profile.avoidedStyles && profile.avoidedStyles.length > 0 && (
              <div>
                <div style={{ ...sectionLabel, color: OXBLOOD }}>Avoided</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {profile.avoidedStyles.map((style, i) => (
                    <span key={i} style={{ ...tagStyle, borderColor: OXBLOOD, color: OXBLOOD }}>{style}</span>
                  ))}
                </div>
              </div>
            )}

            {profile.budgetMin != null && profile.budgetMax != null && (
              <div style={{ borderTop: `1px solid ${RULE}`, paddingTop: 12 }}>
                <div style={sectionLabel}>Typical Spend</div>
                <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: typeScale.h2, color: INK }}>
                  ${profile.budgetMin} – ${profile.budgetMax}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div
            style={{
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.body,
              color: INK_SOFT,
              marginBottom: 20,
              borderTop: `1px solid ${RULE}`,
              paddingTop: 12,
            }}
          >
            Profile saved, but not enough tasting data to infer preferences yet.
          </div>
        )}

        <button onClick={() => onSuccess(result)} style={submitBtn(true)}>
          Continue
        </button>
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
            fontSize: typeScale.micro,
            letterSpacing: 3,
            textTransform: 'uppercase',
            color: OXBLOOD,
            marginBottom: 4,
          }}
        >
          Step 2 · Tasting History
        </div>
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.body,
            color: INK_SOFT,
          }}
        >
          Upload a CellarTracker tasting history export to refine your taste profile. Optional — skip to proceed.
        </div>
      </div>

      {error && (
        <div
          style={{
            border: `1px solid ${RULE}`,
            padding: '10px 16px',
            marginBottom: 16,
            fontFamily: "'EB Garamond', serif",
            fontSize: typeScale.body,
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
                Uploading profile…
              </>
            ) : (
              'Upload & Continue'
            )}
          </button>

          <button type="button" onClick={onSkip} style={skipBtn}>
            Skip
          </button>
        </div>
      </form>
    </div>
  );
};

export default UploadTastingHistoryScreen;
