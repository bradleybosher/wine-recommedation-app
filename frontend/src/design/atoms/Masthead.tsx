import { INK, INK_SOFT } from '@/design/tokens';

interface Props {
  small?: boolean;
  dateline?: string;
}

export default function Masthead({ small = false, dateline = 'A Private Cellar Review' }: Props) {
  const padding = small ? '18px 32px 12px' : '28px 40px 14px';
  const titleSize = small ? 36 : 56;

  return (
    <div style={{ borderBottom: `2px solid ${INK}`, padding, textAlign: 'center', fontFamily: "'Cormorant Garamond', serif" }}>
      <div style={{ fontSize: 10, letterSpacing: 6, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 4 }}>
        Volume XII · Number IV
      </div>
      <div style={{ fontSize: titleSize, fontWeight: 500, letterSpacing: -1, lineHeight: 0.95, color: INK }}>
        Vinothèque
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 8 }}>
        <span style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: 11, color: INK_SOFT }}>
          {dateline}
        </span>
        <span style={{ fontSize: 10, letterSpacing: 3, textTransform: 'uppercase', color: INK_SOFT }}>
          Est. MMXIV
        </span>
      </div>
    </div>
  );
}
