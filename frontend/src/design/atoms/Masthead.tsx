import { INK, INK_SOFT, space, typeScale } from '@/design/tokens';

interface Props {
  small?: boolean;
  dateline?: string;
}

export default function Masthead({ small = false, dateline = 'A Private Cellar Review' }: Props) {
  const padding = small ? `${space.sm} 0 ${space.xs}` : `${space.md} 0 ${space.sm}`;
  const titleSize = small ? typeScale.h1 : typeScale.display;

  return (
    <div style={{ borderBottom: `2px solid ${INK}`, padding, textAlign: 'center', fontFamily: "'Cormorant Garamond', serif" }}>
      <div style={{ fontSize: typeScale.micro, letterSpacing: 6, textTransform: 'uppercase', color: INK_SOFT, marginBottom: 4 }}>
        Volume XII · Number IV
      </div>
      <div style={{ fontSize: titleSize, fontWeight: 500, letterSpacing: -1, lineHeight: 0.95, color: INK }}>
        Vinothèque
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 8, gap: space.xs, flexWrap: 'wrap' }}>
        <span style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic', fontSize: typeScale.label, color: INK_SOFT }}>
          {dateline}
        </span>
        <span style={{ fontSize: typeScale.micro, letterSpacing: 3, textTransform: 'uppercase', color: INK_SOFT }}>
          Est. MMXIV
        </span>
      </div>
    </div>
  );
}
