import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import type { RecommendationResponse } from '@/client/types.gen';

interface RecommendationContextValue {
  recommendations: RecommendationResponse | null;
  setRecommendations: (r: RecommendationResponse) => void;
}

const RecommendationContext = createContext<RecommendationContextValue | null>(null);

export function RecommendationProvider({ children }: { children: ReactNode }) {
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  // Stable reference so consumers only re-render when recommendations actually change
  // (setRecommendations from useState is already stable).
  const value = useMemo(() => ({ recommendations, setRecommendations }), [recommendations]);
  return (
    <RecommendationContext.Provider value={value}>
      {children}
    </RecommendationContext.Provider>
  );
}

export function useRecommendations(): RecommendationContextValue {
  const ctx = useContext(RecommendationContext);
  if (!ctx) throw new Error('useRecommendations must be used within RecommendationProvider');
  return ctx;
}
