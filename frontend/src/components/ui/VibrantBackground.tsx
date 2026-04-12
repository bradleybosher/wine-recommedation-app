import React from 'react';

export default function VibrantBackground({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Base gradient */}
      <div className="absolute inset-0 z-0 bg-gradient-to-br from-wine-purple-deep via-wine-burgundy to-slate-900" />
      {/* Animated blobs */}
      <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-wine-burgundy/40 blur-3xl animate-[blob-drift_14s_ease-in-out_infinite]" />
      <div className="absolute top-12 right-0 w-80 h-80 rounded-full bg-wine-purple-mid/35 blur-3xl animate-[blob-drift-slow_18s_ease-in-out_infinite]" />
      <div className="absolute bottom-24 left-1/3 w-72 h-72 rounded-full bg-wine-amber/25 blur-3xl animate-[blob-drift_22s_ease-in-out_infinite_reverse]" />
      <div className="absolute bottom-0 right-8 w-64 h-64 rounded-full bg-wine-rose/20 blur-3xl animate-[blob-drift-slow_16s_ease-in-out_infinite_2s]" />
      {/* Content */}
      <div className="relative z-10 min-h-screen">{children}</div>
    </div>
  );
}
