import React, { useState } from 'react';
import FileUploader from './FileUploader';
import { uploadInventoryUploadInventoryPost, getInventoryInventoryGet } from './client';
import type { UploadInventoryResponse, InventoryResponse } from './client/types.gen';

interface UploadInventoryScreenProps {
  onSuccess: (response: UploadInventoryResponse) => void;
}

const UploadInventoryScreen: React.FC<UploadInventoryScreenProps> = ({ onSuccess }) => {
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
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-green-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Cellar Inventory Loaded</h2>
          <p className="text-gray-600 mb-6">{result.message}</p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-lg font-semibold text-blue-900">
              {result.count} {result.count === 1 ? 'bottle' : 'bottles'} found
            </p>
            {ageHours !== null && ageHours !== undefined && (
              <p className="text-sm text-blue-700 mt-2">
                Export from {getAgeDescription(ageHours)}
              </p>
            )}
          </div>

          {stale && (
            <div className="bg-amber-50 border border-amber-400 rounded-lg p-4 text-left">
              <div className="flex gap-3">
                <svg className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <div>
                  <p className="font-semibold text-amber-900">Your inventory may be outdated</p>
                  <p className="text-sm text-amber-800 mt-1">
                    This export is older than a few weeks. Consider uploading a fresh CellarTracker export for more accurate recommendations.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Step 1: Your Cellar Inventory</h2>
      <p className="text-gray-600 mb-6">
        Upload a CellarTracker export (TSV file) of your wine collection. We'll analyze your cellar to understand your taste preferences.
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

        <button
          type="submit"
          disabled={!fileData.file || isLoading}
          className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-lg font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 ${
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
              Uploading inventory...
            </div>
          ) : (
            'Upload & Continue'
          )}
        </button>
      </form>
    </div>
  );
};

export default UploadInventoryScreen;