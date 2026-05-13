import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import UploadFlow from './UploadFlow';
import ErrorBoundary from '@/components/ErrorBoundary';
import { getInventoryInventoryGet } from './client';
import VibrantBackground from '@/components/ui/VibrantBackground';
import { Loader2 } from 'lucide-react';
import './index.css';

const DebugPanel = React.lazy(() => import('./DebugPanel'));
const showDebugPanel = import.meta.env.VITE_SHOW_DEBUG === 'true';

export default function App() {
  const [inventoryState, setInventoryState] = useState<'loading' | 'empty' | 'populated'>('loading');

  useEffect(() => {
    const checkInventory = async () => {
      try {
        const response = await getInventoryInventoryGet();

        if (response?.data?.bottles?.length) {
          setInventoryState('populated');
        } else {
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

  if (inventoryState === 'populated') {
    return <Navigate to="/preferences" replace />;
  }

  return (
    <VibrantBackground>
      <ErrorBoundary>
        <UploadFlow onComplete={handleUploadFlowComplete} />
      </ErrorBoundary>

      {showDebugPanel && (
        <React.Suspense fallback={null}>
          <DebugPanel />
        </React.Suspense>
      )}
    </VibrantBackground>
  );
}
