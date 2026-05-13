import type { ReactNode } from 'react';
import { INK, INK_SOFT } from '@/design/tokens';

interface PanelProps {
  title: string;
  caption: string;
  children: ReactNode;
}

export default function Panel({ title, caption, children }: PanelProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '0 14px',
      }}
    >
      <div
        style={{
          fontFamily: "'Cormorant Garamond', serif",
          fontStyle: 'italic',
          fontSize: 11,
          letterSpacing: 3,
          textTransform: 'uppercase',
          color: INK_SOFT,
          marginBottom: 2,
        }}
      >
        {caption}
      </div>
      <div
        style={{
          fontFamily: "'Cormorant Garamond', serif",
          fontSize: 22,
          color: INK,
          marginBottom: 14,
        }}
      >
        {title}
      </div>
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
        }}
      >
        {children}
      </div>
    </div>
  );
}
