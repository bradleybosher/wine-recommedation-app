import { INK } from '@/design/tokens';

interface Props {
  size?: number;
  color?: string;
}

export default function Fleuron({ size = 26, color = INK }: Props) {
  return (
    <svg viewBox="0 0 40 20" width={size * 2} height={size} style={{ display: 'inline-block' }}>
      <path d="M0 10 L 14 10 M 26 10 L 40 10" stroke={color} strokeWidth={0.7} />
      <path d="M 20 4 Q 16 10 20 16 Q 24 10 20 4 Z" fill={color} opacity={0.9} />
      <circle cx={20} cy={10} r={1.2} fill={color} />
      <circle cx={14.5} cy={10} r={0.9} fill={color} />
      <circle cx={25.5} cy={10} r={0.9} fill={color} />
    </svg>
  );
}
