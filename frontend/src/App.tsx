import React, { useEffect, useState } from 'react';
import RecommendationScreen from './RecommendationScreen';
import UploadFlow from './UploadFlow';
import { getInventoryInventoryGet } from './client';
import type { InventoryResponse } from './client/types.gen';
import VibrantBackground from '@/components/ui/VibrantBackground';
import { Loader2 } from 'lucide-react';
import './index.css';

const DebugPanel = React.lazy(() => import('./DebugPanel'));
const showDebugPanel = import.meta.env.VITE_SHOW_DEBUG === 'true';

export default function App() {
  const [inventoryState, setInventoryState] = useState<'loading' | 'empty' | 'populated'>('loading');
  const [inventory, setInventory] = useState<InventoryResponse | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const checkInventory = async () => {
      try {
        const response = await getInventoryInventoryGet();

        if (response && response.data) {
          const data = response.data;
          setInventory(data);

          // Check if inventory is empty
          if (!data.bottles || data.bottles.length === 0) {
            setInventoryState('empty');
          } else {
            setInventoryState('populated');
          }
        } else {
          // No data or empty response
          setInventoryState('empty');
        }
      } catch (err: any) {
        // If we get an error (e.g., 404), treat inventory as empty
        console.log('No inventory found, showing upload flow');
        setInventoryState('empty');
      }
    };

    checkInventory();
  }, []);

  const handleUploadFlowComplete = () => {
    setInventoryState('populated');
  };

  const handleUpdateProfile = () => {
    setInventoryState('empty');
  };

  if (inventoryState === 'loading') {
    return (
      <VibrantBackground>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <Loader2 className="animate-spin h-12 w-12 text-wine-rose mx-auto mb-4" strokeWidth={1.5} />
            <p className="text-white/70">Loading...</p>
          </div>
        </div>
      </VibrantBackground>
    );
  }

  return (
    <VibrantBackground>
      {error && (
        <div className="bg-wine-burgundy/30 border border-wine-rose/40 text-white/90 px-4 py-3">
          <strong className="font-bold">Error: </strong>
          <span>{error}</span>
        </div>
      )}

      {inventoryState === 'empty' ? (
        <UploadFlow onComplete={handleUploadFlowComplete} />
      ) : (
        <div className="p-8">
          <RecommendationScreen onUpdateProfile={handleUpdateProfile} />
        </div>
      )}

      {showDebugPanel && (
        <React.Suspense fallback={null}>
          <DebugPanel />
        </React.Suspense>
      )}
    </VibrantBackground>
  );
}
