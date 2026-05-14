import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import UploadFlow from './UploadFlow';
import ErrorBoundary from '@/components/ErrorBoundary';
import { getInventoryInventoryGet } from './client';
import { Loader2 } from 'lucide-react';
import { INK, INK_SOFT, PAPER } from '@/design/tokens';
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
      <div
        style={{
          minHeight: '100vh',
          background: PAPER,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 12,
        }}
      >
        <Loader2
          className="animate-spin"
          style={{ width: 28, height: 28, color: INK }}
          strokeWidth={1.5}
        />
        <div
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: 13,
            color: INK_SOFT,
          }}
        >
          Loading…
        </div>
      </div>
    );
  }

  if (inventoryState === 'populated') {
    return <Navigate to="/preferences" replace />;
  }

  return (
    <>
      <ErrorBoundary>
        <UploadFlow onComplete={handleUploadFlowComplete} />
      </ErrorBoundary>

      {showDebugPanel && (
        <React.Suspense fallback={null}>
          <DebugPanel />
        </React.Suspense>
      )}
    </>
  );
}
