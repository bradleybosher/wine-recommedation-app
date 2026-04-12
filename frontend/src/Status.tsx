import React, { useState, useEffect } from 'react';
import { getInventoryInventoryGet } from './client';
import type { InventoryResponse } from './client/types.gen';

const Status: React.FC = () => {
  const [inventoryData, setInventoryData] = useState<InventoryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInventory = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await getInventoryInventoryGet();
      // The response is of type GetInventoryInventoryGetResponse which is InventoryResponse
      setInventoryData(response as InventoryResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch inventory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  const getBottleCount = (): number => {
    if (!inventoryData?.bottles) return 0;
    return inventoryData.bottles.length;
  };

  const getDataFreshness = (): string => {
    if (!inventoryData) return 'Unknown';
    return inventoryData.stale ? 'Stale' : 'Fresh';
  };

  const getAgeHours = (): string => {
    if (!inventoryData?.ageHours) return 'Unknown';
    return `${inventoryData.ageHours} hours`;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Wine Database Status</h2>
        <button
          onClick={fetchInventory}
          disabled={loading}
          className="px-4 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {loading && !inventoryData && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-800"></div>
          <p className="mt-2 text-gray-600">Loading inventory data...</p>
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
              <h3 className="text-sm font-medium text-red-800">Error loading inventory</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {inventoryData && !loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
              <div className="text-sm font-medium text-blue-600 mb-1">Total Wines in Database</div>
              <div className="text-3xl font-bold text-blue-900">{getBottleCount()}</div>
              <div className="text-xs text-blue-700 mt-1">
                {inventoryData.bottles ? `${inventoryData.bottles.length} bottles` : 'No bottles'}
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <div className="text-sm font-medium text-gray-600 mb-1">Data Freshness</div>
              <div className="flex items-center">
                <div className={`h-3 w-3 rounded-full mr-2 ${inventoryData.stale ? 'bg-yellow-500' : 'bg-green-500'}`}></div>
                <span className={`text-xl font-bold ${inventoryData.stale ? 'text-yellow-800' : 'text-green-800'}`}>
                  {getDataFreshness()}
                </span>
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {inventoryData.stale ? 'Data may be outdated' : 'Data is current'}
              </div>
            </div>
            
            <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
              <div className="text-sm font-medium text-purple-600 mb-1">Data Age</div>
              <div className="text-2xl font-bold text-purple-900 font-mono">
                {getAgeHours()}
              </div>
              <div className="text-xs text-purple-700 mt-1">
                Since last update
              </div>
            </div>
          </div>

          <div className="text-xs text-gray-500 pt-4 border-t border-gray-100">
            <div className="flex justify-between">
              <span>Last updated: {new Date().toLocaleTimeString()}</span>
              <span>Using generated client: GET /inventory</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Status;