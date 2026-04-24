import React, { useState } from 'react';
import FileUploader from './FileUploader';
import MealDescriptionInput from './MealDescriptionInput';
import RecommendationResults from './RecommendationResults';
<<<<<<< HEAD
import ProfileTab from './ProfileTab';
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
import { recommendRecommendPost } from '@/client';
import type { RecommendationResponse } from '@/client/types.gen';
import GlassCard from '@/components/ui/GlassCard';
import { Loader2 } from 'lucide-react';

interface RecommendationScreenProps {
  onUpdateProfile?: () => void;
}

const RecommendationScreen: React.FC<RecommendationScreenProps> = ({ onUpdateProfile }) => {
<<<<<<< HEAD
  const [activeTab, setActiveTab] = useState<'recommend' | 'profile'>('recommend');

=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
  // Consolidated file state
  const [fileData, setFileData] = useState({
    file: null as File | null,
    previewUrl: '',
    base64: ''
  });

  // State for meal description
  const [mealDescription, setMealDescription] = useState('');

  // State for style overrides (advanced option)
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [styleOverrides, setStyleOverrides] = useState('');

  // State for API submission
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [recommendationResponse, setRecommendationResponse] = useState<RecommendationResponse | null>(null);

  // --- File Upload Handler ---
  const handleFileChange = (file: File | null, previewUrl: string, base64: string, errorMsg: string) => {
    setFileData({
      file,
      previewUrl,
      base64
    });
    if (errorMsg) {
      setError(errorMsg);
    } else if (error) {
      setError('');
    }
  };

  // --- Meal Description Handler ---
  const handleMealDescriptionChange = (value: string) => {
    setMealDescription(value);
    if (error) setError('');
  };

  // --- Style Overrides Handler ---
  const handleStyleOverridesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setStyleOverrides(e.target.value);
  };


  // --- Form Submission ---
  const isSubmitDisabled = !fileData.file || mealDescription.trim() === '';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitDisabled) return;

    setIsLoading(true);
    setError('');
    setRecommendationResponse(null);

    try {
      const requestBody = {
        wine_list: fileData.file!,
        meal: mealDescription.trim(),
        ...(styleOverrides.trim() && { style_terms: styleOverrides.trim() })
      };

      const response = await recommendRecommendPost({
        body: requestBody
      });

      if (!response?.data) {
        throw new Error('No response received from server');
      }

      setRecommendationResponse(response.data);
    } catch (err: any) {
      if (err instanceof Error) {
        setError(err.message);
      } else if (err.data?.detail) {
        setError(err.data.detail);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewSearch = () => {
    setFileData({ file: null, previewUrl: '', base64: '' });
    setMealDescription('');
    setStyleOverrides('');
    setRecommendationResponse(null);
    setError('');
    setIsLoading(false);
    setShowAdvanced(false);
  };

  // --- Render ---
  return (
    <div className="p-4 md:p-8 font-sans">
      <GlassCard className="max-w-4xl mx-auto p-6 md:p-10">
<<<<<<< HEAD
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
=======
        <div className="flex items-center justify-between mb-8">
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-center mb-2 text-white">Wine Recommendations</h1>
            <p className="text-center text-white/70">Upload a restaurant wine list (PDF or photo) to find wines that match your taste</p>
          </div>
          {onUpdateProfile && (
            <button
              onClick={onUpdateProfile}
              className="ml-4 px-4 py-2 text-sm text-white/70 hover:text-white hover:bg-glass-surface-hover rounded-md border border-glass-border transition-colors whitespace-nowrap"
            >
              Update Profile
            </button>
          )}
        </div>

<<<<<<< HEAD
        {/* Tab Bar */}
        <div className="flex border-b border-glass-border mb-8">
          {(['recommend', 'profile'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2 text-sm font-medium transition-colors focus:outline-none ${
                activeTab === tab
                  ? 'border-b-2 border-wine-gold text-white -mb-px'
                  : 'text-white/50 hover:text-white/80'
              }`}
            >
              {tab === 'recommend' ? 'Recommend' : 'My Profile'}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'profile' ? (
          <ProfileTab />
        ) : (
          <>
            {error && (
              <div className="bg-wine-burgundy/30 border border-wine-rose/40 text-white/90 px-4 py-3 rounded-xl relative mb-6" role="alert">
                <strong className="font-bold">Error: </strong>
                <span className="block sm:inline">{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* 1. File Upload */}
              <FileUploader
                onFileChange={handleFileChange}
                file={fileData.file}
                previewUrl={fileData.previewUrl}
                error={error}
              />

              {/* 2. Meal Description */}
              <MealDescriptionInput
                mealDescription={mealDescription}
                onMealDescriptionChange={handleMealDescriptionChange}
                error={error}
              />

              {/* 3. Style Overrides (Advanced Option) */}
              <div className="mt-6">
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="text-sm text-wine-gold hover:text-wine-amber focus:outline-none focus:ring-2 focus:ring-wine-rose rounded"
                >
                  {showAdvanced ? 'Hide Advanced Options' : 'Show Advanced Options'}
                </button>
                {showAdvanced && (
                  <div className="mt-4">
                    <label htmlFor="style-overrides" className="block text-lg font-medium text-white/80 mb-2">
                      Style Overrides (Optional)
                    </label>
                    <input
                      type="text"
                      id="style-overrides"
                      value={styleOverrides}
                      onChange={handleStyleOverridesChange}
                      placeholder="e.g., mineral whites, savoury reds, grower champagne"
                      className="shadow-sm focus:ring-wine-rose focus:border-wine-rose block w-full sm:text-sm border-glass-border rounded-md p-3 bg-glass-surface text-white placeholder:text-white/40"
                    />
                    <p className="text-xs text-white/50 mt-1">Enter terms separated by commas.</p>
                  </div>
                )}
              </div>

              {/* 4. Submit Button */}
              <div className="pt-4">
                <button
                  type="submit"
                  disabled={isSubmitDisabled || isLoading}
                  className={`w-full flex justify-center py-3 px-4 border rounded-md shadow-sm text-lg font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors ${
                    isSubmitDisabled || isLoading
                      ? 'bg-white/10 text-white/30 cursor-not-allowed border-white/10'
                      : 'bg-wine-burgundy hover:bg-wine-merlot border-wine-rose/30 focus:ring-wine-rose shadow-[0_0_20px_rgba(139,37,70,0.4)]'
                  }`}
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" strokeWidth={1.5} />
                      Analyzing wine list...
                    </div>
                  ) : (
                    'Get Recommendations'
                  )}
                </button>
              </div>
            </form>

            {/* 5. Results Display */}
            {recommendationResponse && (
              <RecommendationResults
                response={recommendationResponse}
                onNewSearch={handleNewSearch}
              />
            )}
          </>
=======
        {error && (
          <div className="bg-wine-burgundy/30 border border-wine-rose/40 text-white/90 px-4 py-3 rounded-xl relative mb-6" role="alert">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 1. File Upload */}
          <FileUploader
            onFileChange={handleFileChange}
            file={fileData.file}
            previewUrl={fileData.previewUrl}
            error={error}
          />

          {/* 2. Meal Description */}
          <MealDescriptionInput
            mealDescription={mealDescription}
            onMealDescriptionChange={handleMealDescriptionChange}
            error={error}
          />

          {/* 3. Style Overrides (Advanced Option) */}
          <div className="mt-6">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-wine-gold hover:text-wine-amber focus:outline-none focus:ring-2 focus:ring-wine-rose rounded"
            >
              {showAdvanced ? 'Hide Advanced Options' : 'Show Advanced Options'}
            </button>
            {showAdvanced && (
              <div className="mt-4">
                <label htmlFor="style-overrides" className="block text-lg font-medium text-white/80 mb-2">
                  Style Overrides (Optional)
                </label>
                <input
                  type="text"
                  id="style-overrides"
                  value={styleOverrides}
                  onChange={handleStyleOverridesChange}
                  placeholder="e.g., mineral whites, savoury reds, grower champagne"
                  className="shadow-sm focus:ring-wine-rose focus:border-wine-rose block w-full sm:text-sm border-glass-border rounded-md p-3 bg-glass-surface text-white placeholder:text-white/40"
                />
                <p className="text-xs text-white/50 mt-1">Enter terms separated by commas.</p>
              </div>
            )}
          </div>

          {/* 4. Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              disabled={isSubmitDisabled || isLoading}
              className={`w-full flex justify-center py-3 px-4 border rounded-md shadow-sm text-lg font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors ${
                isSubmitDisabled || isLoading
                  ? 'bg-white/10 text-white/30 cursor-not-allowed border-white/10'
                  : 'bg-wine-burgundy hover:bg-wine-merlot border-wine-rose/30 focus:ring-wine-rose shadow-[0_0_20px_rgba(139,37,70,0.4)]'
              }`}
            >
              {isLoading ? (
                <div className="flex items-center">
                  <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" strokeWidth={1.5} />
                  Analyzing wine list...
                </div>
              ) : (
                'Get Recommendations'
              )}
            </button>
          </div>
        </form>

        {/* 5. Results Display */}
        {recommendationResponse && (
          <RecommendationResults
            response={recommendationResponse}
            onNewSearch={handleNewSearch}
          />
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
        )}
      </GlassCard>
    </div>
  );
};

export default RecommendationScreen;
