import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import UploadFlow from './UploadFlow';
import ErrorBoundary from '@/components/ErrorBoundary';
import { getInventoryInventoryGet, profileSummaryProfileSummaryGet } from './client';
import { Loader2 } from 'lucide-react';
import { INK, INK_SOFT, PAPER, typeScale } from '@/design/tokens';
import { useProfiles } from '@/state/profileStore';
import './index.css';

const DebugPanel = React.lazy(() => import('./DebugPanel'));
const showDebugPanel = import.meta.env.VITE_SHOW_DEBUG === 'true';

const ESTABLISHED_SOURCES = new Set(['seed_bottles', 'cellartracker_synthesized']);

export default function App() {
  const { activeProfileId } = useProfiles();
  const [inventoryState, setInventoryState] = useState<'loading' | 'empty' | 'populated'>('loading');

  useEffect(() => {
    if (!activeProfileId) {
      setInventoryState('loading');
      return;
    }
    let cancelled = false;
    setInventoryState('loading');
    (async () => {
      try {
        const [invResponse, summaryResponse] = await Promise.all([
          getInventoryInventoryGet(),
          profileSummaryProfileSummaryGet(),
        ]);
        if (cancelled) return;
        const hasInventory = Boolean(invResponse?.data?.bottles?.length);
        const profileSource = summaryResponse?.data?.profileSource ?? '';
        const hasEstablishedProfile = ESTABLISHED_SOURCES.has(profileSource);
        if (hasInventory || hasEstablishedProfile) {
          setInventoryState('populated');
        } else {
          setInventoryState('empty');
        }
      } catch {
        if (cancelled) return;
        setInventoryState('empty');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [activeProfileId]);

  const handleUploadFlowComplete = () => {
    setInventoryState('populated');
  };

  if (inventoryState === 'loading') {
    return (
      <div
        style={{
          minHeight: '100dvh',
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
            fontSize: typeScale.body,
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
