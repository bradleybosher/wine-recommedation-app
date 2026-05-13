import type { ReactNode } from 'react';
import { PAPER, PAPER_DEEP } from '@/design/tokens';

interface Props {
  children: ReactNode;
  className?: string;
}

export default function PaperFrame({ children, className }: Props) {
  return (
    <div
      className={className}
      style={{
        background: `radial-gradient(ellipse at 60% 80%, ${PAPER_DEEP} 0%, ${PAPER} 70%)`,
        border: '1px solid rgba(80,40,10,0.12)',
        boxShadow: 'inset 0 0 80px rgba(80,40,10,0.06)',
        minHeight: '100vh',
        position: 'relative',
        fontFamily: "'EB Garamond', 'Cormorant Garamond', serif",
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
      <div style={{ position: 'relative', zIndex: 1 }}>{children}</div>
    </div>
  );
}
