import { INK, INK_SOFT, OXBLOOD } from '@/design/tokens';

interface Props {
  label: string;
  value: string;
  small?: boolean;
  inkAccent?: boolean;
}

export default function Field({ label, value, small = false, inkAccent = false }: Props) {
  return (
    <div style={{ fontFamily: "'Cormorant Garamond', serif" }}>
      <div
        style={{
          fontSize: 9,
          letterSpacing: 3,
          textTransform: 'uppercase',
          color: INK_SOFT,
          opacity: 0.85,
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: small ? 18 : 22,
          color: inkAccent ? OXBLOOD : INK,
          fontStyle: inkAccent ? 'italic' : 'normal',
          borderBottom: `1px solid ${INK}`,
          paddingBottom: 4,
        }}
      >
        {value}
      </div>
    </div>
  );
}
