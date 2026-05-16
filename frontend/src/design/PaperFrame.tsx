import type { ReactNode } from 'react';
import { PAGE_MAX_WIDTH, PAPER, PAPER_DEEP, space, typeScale, lineHeight } from '@/design/tokens';

interface Props {
  children: ReactNode;
  className?: string;
  /** Skip the centered max-width inner container (full-bleed pages). */
  bleed?: boolean;
}

export default function PaperFrame({ children, className, bleed = false }: Props) {
  return (
    <div
      className={className}
      style={{
        background: `radial-gradient(ellipse at 60% 80%, ${PAPER_DEEP} 0%, ${PAPER} 70%)`,
        border: '1px solid rgba(80,40,10,0.12)',
        boxShadow: 'inset 0 0 80px rgba(80,40,10,0.06)',
        minHeight: '100dvh',
        position: 'relative',
        fontFamily: "'EB Garamond', 'Cormorant Garamond', serif",
        fontSize: typeScale.body,
        lineHeight: lineHeight.body,
      }}
    >
      {/* paper texture overlay */}
      <div
        aria-hidden
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(rgba(80,40,10,0.025) 1px, transparent 1px)',
          backgroundSize: '3px 3px',
          mixBlendMode: 'multiply',
          pointerEvents: 'none',
        }}
      />
      <div
        style={
          bleed
            ? { position: 'relative', zIndex: 1 }
            : {
                position: 'relative',
                zIndex: 1,
                maxWidth: PAGE_MAX_WIDTH,
                margin: '0 auto',
                padding: `${space.lg} ${space.lg}`,
              }
        }
      >
        {children}
      </div>
    </div>
  );
}
