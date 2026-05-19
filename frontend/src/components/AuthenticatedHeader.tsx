import { INK, PAPER, RULE, space } from '@/design/tokens';
import { useAuth } from '@/state/authStore';
import ProfileSwitcher from './ProfileSwitcher';

export default function AuthenticatedHeader() {
  const { status } = useAuth();
  if (status !== 'authenticated') return null;

  return (
    <div
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 40,
        display: 'flex',
        justifyContent: 'flex-end',
        alignItems: 'center',
        padding: `${space.xs} ${space.md}`,
        background: PAPER,
        borderBottom: `1px solid ${RULE}`,
        color: INK,
      }}
    >
      <ProfileSwitcher />
    </div>
  );
}
