import React, { useState } from 'react';
import FileUploader from './FileUploader';
import { uploadProfileUploadProfilePost } from './client';
import type { UploadProfileResponse } from './client/types.gen';

interface UploadProfileScreenProps {
  onSuccess: (response: UploadProfileResponse) => void;
  onSkip: () => void;
}

const UploadProfileScreen: React.FC<UploadProfileScreenProps> = ({ onSuccess, onSkip }) => {
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
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-6">
          <svg className="mx-auto h-12 w-12 text-green-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          <h2 className="text-2xl font-bold text-gray-900 mb-1">Taste Profile Refined</h2>
          <p className="text-gray-500 text-sm">{result.message}</p>
        </div>

        {hasProfileData ? (
          <div className="space-y-4 mb-6">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Inferred Preferences</h3>

            {profile.preferredGrapes && profile.preferredGrapes.length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-xs font-medium text-gray-500 mb-2">Grapes</p>
                <div className="flex flex-wrap gap-2">
                  {profile.preferredGrapes.map((grape, i) => (
                    <span key={i} className="px-3 py-1 bg-indigo-100 text-indigo-800 text-sm font-medium rounded-full capitalize">
                      {grape}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {profile.preferredRegions && profile.preferredRegions.length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-xs font-medium text-gray-500 mb-2">Regions</p>
                <div className="flex flex-wrap gap-2">
                  {profile.preferredRegions.map((region, i) => (
                    <span key={i} className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full capitalize">
                      {region}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {profile.preferredStyles && profile.preferredStyles.length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-xs font-medium text-gray-500 mb-2">Style Descriptors</p>
                <div className="flex flex-wrap gap-2">
                  {profile.preferredStyles.map((style, i) => (
                    <span key={i} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full capitalize">
                      {style}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {profile.avoidedStyles && profile.avoidedStyles.length > 0 && (
              <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                <p className="text-xs font-medium text-red-700 mb-2">Avoided Styles</p>
                <div className="flex flex-wrap gap-2">
                  {profile.avoidedStyles.map((style, i) => (
                    <span key={i} className="px-3 py-1 bg-red-100 text-red-800 text-sm font-medium rounded-full capitalize">
                      {style}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {profile.budgetMin != null && profile.budgetMax != null && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-xs font-medium text-gray-500 mb-1">Typical Spend</p>
                <p className="text-lg font-semibold text-gray-900">${profile.budgetMin} – ${profile.budgetMax} per bottle</p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-yellow-800">
              Profile saved, but not enough tasting data to infer preferences yet. Add more exports (notes, consumed) to improve recommendations.
            </p>
          </div>
        )}

        <button
          onClick={() => onSuccess(result)}
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-lg font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Continue
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Step 2: Refine Your Taste Profile</h2>
      <p className="text-gray-600 mb-6">
        Upload tasting notes or a separate CellarTracker export to refine your taste profile. (Optional—use the same file again, or skip to proceed)
      </p>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
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
            className={`flex-1 flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-lg font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              !fileData.file || isLoading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500'
            }`}
          >
            {isLoading ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 8l3-4.709z"></path>
                </svg>
                Uploading profile...
              </div>
            ) : (
              'Upload Profile'
            )}
          </button>

          <button
            type="button"
            onClick={onSkip}
            className="flex-1 flex justify-center py-3 px-4 border border-gray-300 rounded-md shadow-sm text-lg font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Skip for Now
          </button>
        </div>
      </form>
    </div>
  );
};

export default UploadProfileScreen;