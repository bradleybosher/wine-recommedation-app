import React, { useState, useEffect } from 'react';
import { profileSummaryProfileSummaryGet, type ProfileSummaryResponse } from '@/client';

const ProfileSummaryView = () => {
  const [profileData, setProfileData] = useState<ProfileSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProfileData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await profileSummaryProfileSummaryGet();
      setProfileData(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to load profile data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfileData();
  }, []);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Profile Summary</h2>
        <button
          onClick={loadProfileData}
          disabled={loading}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {loading && !profileData && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-800"></div>
          <p className="mt-2 text-gray-600">Loading profile data...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading profile</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {profileData && !loading && (
        <div className="space-y-6">
          {/* Top Varietals */}
          {profileData.topVarietals && profileData.topVarietals.length > 0 && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Top Varietals</h3>
              <div className="flex flex-wrap gap-2">
                {profileData.topVarietals.map((varietal, index) => (
                  <span key={index} className="px-3 py-1 bg-indigo-100 text-indigo-800 text-sm font-medium rounded-full">
                    {varietal}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Top Regions */}
          {profileData.topRegions && profileData.topRegions.length > 0 && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Top Regions</h3>
              <div className="flex flex-wrap gap-2">
                {profileData.topRegions.map((region, index) => (
                  <span key={index} className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                    {region}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Top Producers */}
          {profileData.topProducers && profileData.topProducers.length > 0 && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Top Producers</h3>
              <div className="space-y-2">
                {profileData.topProducers.map((producer, index) => (
                  <div key={index} className="flex items-center text-sm text-gray-700">
                    <span className="w-6 h-6 flex items-center justify-center bg-orange-100 text-orange-800 rounded-full mr-2 text-xs font-bold">
                      {index + 1}
                    </span>
                    {producer}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Preferred Descriptors */}
          {profileData.preferredDescriptors && profileData.preferredDescriptors.length > 0 && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Preferred Descriptors</h3>
              <div className="flex flex-wrap gap-2">
                {profileData.preferredDescriptors.map((descriptor, index) => (
                  <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                    {descriptor}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Avoided Styles */}
          {profileData.avoidedStyles && profileData.avoidedStyles.length > 0 && (
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <h3 className="text-sm font-medium text-red-800 mb-3">Avoided Styles</h3>
              <div className="flex flex-wrap gap-2">
                {profileData.avoidedStyles.map((style, index) => (
                  <span key={index} className="px-3 py-1 bg-red-100 text-red-800 text-sm font-medium rounded-full">
                    {style}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Highly Rated */}
          {profileData.highlyRated && profileData.highlyRated.length > 0 && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Highly Rated Wines</h3>
              <div className="space-y-2">
                {profileData.highlyRated.map((wine, index) => (
                  <div key={index} className="p-2 bg-white rounded border border-gray-200">
                    {Object.entries(wine).map(([key, value]) => (
                      <div key={key} className="text-xs text-gray-700">
                        <span className="font-medium">{key}:</span> {String(value)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Average Spend */}
          {profileData.avgSpend !== null && profileData.avgSpend !== undefined && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Average Spend</h3>
              <div className="text-2xl font-bold text-gray-900">${profileData.avgSpend.toFixed(2)}</div>
            </div>
          )}

          <div className="text-xs text-gray-500 pt-4 border-t border-gray-100">
            <div className="flex justify-between">
              <span>Last updated: {new Date().toLocaleTimeString()}</span>
              <span>Endpoint: GET /profile-summary</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfileSummaryView;