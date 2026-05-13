import { INK, INK_SOFT, OXBLOOD } from '@/design/tokens';

interface Props {
  label: string;
  value: string;
  small?: boolean;
  inkAccent?: boolean;
  onChange?: (value: string) => void;
  placeholder?: string;
}

export default function Field({ label, value, small = false, inkAccent = false, onChange, placeholder }: Props) {
  const valueStyle: React.CSSProperties = {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: small ? 18 : 22,
    color: inkAccent ? OXBLOOD : INK,
    fontStyle: inkAccent ? 'italic' : 'normal',
    borderBottom: `1px solid ${INK}`,
    paddingBottom: 4,
  };

  return (
    <div style={{ fontFamily: "'Cormorant Garamond', serif" }}>
      <div
        style={{
          fontSize: 9,
          letterSpacing: 3,
          textTransform: 'uppercase' as const,
          color: INK_SOFT,
          opacity: 0.85,
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      {onChange ? (
        <input
          type="text"
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          style={{
            ...valueStyle,
            display: 'block',
            width: '100%',
            background: 'transparent',
            border: 'none',
            outline: 'none',
            boxSizing: 'border-box',
          }}
        />
      ) : (
        <div style={valueStyle}>{value}</div>
      )}
    </div>
  );
}
