import React from 'react';

export type WineStyle = 'bordeaux' | 'burgundy' | 'sparkling' | 'generic';

export function getWineStyle(wineName: string, region?: string | null): WineStyle {
  const text = `${wineName} ${region ?? ''}`.toLowerCase();
  if (/champagne|prosecco|cava|sekt|cr[eé]mant|sparkling|p[eé]tillant|fizz|brut/.test(text)) return 'sparkling';
  if (/burgundy|bourgogne|pinot.?noir|chambolle|gevrey|nuits|vosne|pommard|volnay/.test(text)) return 'burgundy';
  if (/bordeaux|cabernet|merlot|m[eé]doc|pauillac|saint.[eé]milion|pomerol|margaux|saint.julien|listrac/.test(text)) return 'bordeaux';
  return 'generic';
}

interface WineBottleIconProps {
  style: WineStyle;
  className?: string;
}

const WineBottleIcon: React.FC<WineBottleIconProps> = ({
  style,
  className = 'h-8 w-5 text-white/60',
}) => {
  const commonProps = {
    viewBox: '0 0 20 50',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.2,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    className,
  };

  if (style === 'bordeaux') {
    return (
      <svg {...commonProps} aria-label="Bordeaux bottle">
        {/* High straight shoulders, classic silhouette */}
        <path d="M 8,2 L 8,5 L 7.5,6 L 7.5,14 L 4,16.5 L 4,46 Q 4,48 10,48 Q 16,48 16,46 L 16,16.5 L 12.5,14 L 12.5,6 L 12,5 L 12,2 Z" />
      </svg>
    );
  }

  if (style === 'burgundy') {
    return (
      <svg {...commonProps} aria-label="Burgundy bottle">
        {/* Long gently sloped shoulders */}
        <path d="M 8,2 L 8,5 L 7.5,6 L 7.5,11 C 7,14 4,17 4,21 L 4,46 Q 4,48 10,48 Q 16,48 16,46 L 16,21 C 16,17 13,14 12.5,11 L 12.5,6 L 12,5 L 12,2 Z" />
      </svg>
    );
  }

  if (style === 'sparkling') {
    return (
      <svg {...commonProps} aria-label="Sparkling bottle">
        {/* Wide body, short neck, wire cage detail */}
        <path d="M 8,4 L 8,7 L 6,9 L 6,13 L 3,16 L 3,46 Q 3,48 10,48 Q 17,48 17,46 L 17,16 L 14,13 L 14,9 L 12,7 L 12,4 Z" />
        {/* Cage wires */}
        <line x1="6" y1="9" x2="14" y2="9" />
        <line x1="6" y1="12" x2="14" y2="12" />
        <line x1="10" y1="7" x2="10" y2="13" />
      </svg>
    );
  }

  // generic — midpoint shape
  return (
    <svg {...commonProps} aria-label="Wine bottle">
      <path d="M 8,2 L 8,5 L 7.5,6 L 7.5,13 L 5,15.5 L 4,18 L 4,46 Q 4,48 10,48 Q 16,48 16,46 L 16,18 L 15,15.5 L 12.5,13 L 12.5,6 L 12,5 L 12,2 Z" />
    </svg>
  );
};

export default WineBottleIcon;
