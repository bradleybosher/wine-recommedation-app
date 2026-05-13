import { INK } from '@/design/tokens';

interface Props {
  color?: string;
  opacity?: number;
}

export default function RuleDouble({ color = INK, opacity = 0.5 }: Props) {
  return (
    <div style={{ borderTop: `1px solid ${color}`, opacity, padding: '2px 0' }}>
      <div style={{ borderTop: `0.5px solid ${color}`, marginTop: 2 }} />
    </div>
  );
}
