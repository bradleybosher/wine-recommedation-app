import React, { useState, useEffect } from 'react';
import { getInventoryInventoryGet, type InventoryResponse } from './client';

interface InventoryData {
  count: number;
  oldest_vintage: string;
  newest_vintage: string;
  stale_flag: boolean;
  bottles: Array<{
    Producer: string;
    Vintage: string;
    Varietal: string;
    Qty: number;
  }>;
}

const InventoryStatusView = () => {
  const [inventoryData, setInventoryData] = useState<InventoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadInventoryData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await getInventoryInventoryGet();
      // The SDK returns the response data directly
      const data = response.data;
      
      // Map the SDK response to the component's expected format
      const mappedData = {
        count: data.bottles?.length || 0,
        oldest_vintage: data.bottles?.reduce((oldest, bottle) => {
          const vintage = parseInt(bottle.vintage || '9999');
          return vintage < oldest ? vintage : oldest;
        }, 9999)?.toString() || 'N/A',
        newest_vintage: data.bottles?.reduce((newest, bottle) => {
          const vintage = parseInt(bottle.vintage || '0');
          return vintage > newest ? vintage : newest;
        }, 0)?.toString() || 'N/A',
        stale_flag: data.stale || false,
        bottles: data.bottles?.map(bottle => ({
          Producer: bottle.producer || 'Unknown',
          Vintage: bottle.vintage || 'N/A',
          Varietal: bottle.varietal || 'Unknown',
          Qty: parseInt(bottle.quantity || '0') || 0
        })) || []
      };
      
      setInventoryData(mappedData);
    } catch (err: any) {
      setError(err.message || 'Failed to load inventory data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInventoryData();
  }, []);

  const formatVintageRange = (oldest: string, newest: string) => {
    if (!oldest || !newest || oldest === 'N/A' || newest === 'N/A') return 'N/A';
    return `${oldest} - ${newest}`;
  };

  const renderSampleBottles = (bottles: Array<{Producer: string; Vintage: string; Varietal: string; Qty: number}>) => {
    if (!bottles || bottles.length === 0) {
      return <div className="text-gray-500 italic">No bottles in inventory</div>;
    }

    const sample = bottles.slice(0, 5);
    
    return (
      <div className="space-y-2">
        {sample.map((bottle, index) => (
          <div key={index} className="border-l-2 border-gray-300 pl-3 py-1">
            <div className="font-mono text-sm">
              <span className="font-semibold">{bottle.Producer || 'Unknown'}</span>
              <span className="text-gray-600"> • {bottle.Vintage || 'N/A'}</span>
              <span className="text-gray-600"> • {bottle.Varietal || 'Unknown'}</span>
              <span className="ml-2 px-2 py-0.5 bg-gray-100 rounded text-xs">
                Qty: {bottle.Qty || 0}
              </span>
            </div>
          </div>
        ))}
        {bottles.length > 5 && (
          <div className="text-gray-500 text-sm italic">
            ...and {bottles.length - 5} more bottles
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Cellar Status</h2>
        <button
          onClick={loadInventoryData}
          disabled={loading}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-gray-500 mb-1">Total Bottles</div>
              <div className="text-3xl font-bold text-gray-900">{inventoryData.count || 0}</div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-gray-500 mb-1">Vintage Range</div>
              <div className="text-2xl font-bold text-gray-900 font-mono">
                {formatVintageRange(inventoryData.oldest_vintage, inventoryData.newest_vintage)}
              </div>
            </div>
            
            <div className={`p-4 rounded-lg ${inventoryData.stale_flag ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'}`}>
              <div className="text-sm font-medium text-gray-500 mb-1">Data Freshness</div>
              <div className="flex items-center">
                <div className={`h-3 w-3 rounded-full mr-2 ${inventoryData.stale_flag ? 'bg-yellow-500' : 'bg-green-500'}`}></div>
                <span className={`font-semibold ${inventoryData.stale_flag ? 'text-yellow-800' : 'text-green-800'}`}>
                  {inventoryData.stale_flag ? 'Stale - Needs Refresh' : 'Fresh'}
                </span>
              </div>
              {inventoryData.stale_flag && (
                <p className="text-sm text-yellow-700 mt-2">
                  Inventory data may be outdated. Consider refreshing from source.
                </p>
              )}
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-700 mb-3">Sample Bottles (First 5)</h3>
            {renderSampleBottles(inventoryData.bottles)}
          </div>

          <div className="text-xs text-gray-500 pt-4 border-t border-gray-100">
            <div className="flex justify-between">
              <span>Last updated: {new Date().toLocaleTimeString()}</span>
              <span>Endpoint: GET /inventory</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryStatusView;