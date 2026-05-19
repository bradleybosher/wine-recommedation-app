import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, LogOut } from 'lucide-react';

import { INK, INK_SOFT, PAPER, RULE, space, typeScale } from '@/design/tokens';
import { useAuth } from '@/state/authStore';
import { useProfiles } from '@/state/profileStore';

export default function ProfileSwitcher() {
  const { user, logout } = useAuth();
  const { profiles, activeProfile, setActiveProfile } = useProfiles();
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    window.addEventListener('mousedown', handleClick);
    return () => window.removeEventListener('mousedown', handleClick);
  }, [open]);

  if (!user || !activeProfile) return null;

  const labelStyle = {
    fontFamily: "'Cormorant Garamond', serif",
    fontSize: typeScale.label,
    letterSpacing: 2,
    textTransform: 'uppercase' as const,
    color: INK,
  };

  return (
    <div ref={wrapRef} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={{
          ...labelStyle,
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          padding: `${space.xs} ${space.sm}`,
          background: 'transparent',
          border: `1px solid ${RULE}`,
          cursor: 'pointer',
        }}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span>{activeProfile.name}</span>
        <ChevronDown style={{ width: 14, height: 14 }} strokeWidth={1.5} />
      </button>

      {open && (
        <div
          role="listbox"
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            right: 0,
            minWidth: 240,
            background: PAPER,
            border: `1px solid ${INK}`,
            zIndex: 50,
            boxShadow: '0 6px 18px rgba(80,40,10,0.10)',
          }}
        >
          <div
            style={{
              padding: `${space.xs} ${space.sm}`,
              fontFamily: "'EB Garamond', serif",
              fontStyle: 'italic',
              fontSize: typeScale.label,
              color: INK_SOFT,
              borderBottom: `1px solid ${RULE}`,
            }}
          >
            {user.email}
          </div>
          {profiles.map((p) => {
            const isActive = p.id === activeProfile.id;
            return (
              <button
                key={p.id}
                type="button"
                role="option"
                aria-selected={isActive}
                onClick={() => {
                  setActiveProfile(p.id);
                  setOpen(false);
                }}
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  padding: `${space.xs} ${space.sm}`,
                  fontFamily: "'EB Garamond', serif",
                  fontSize: typeScale.body,
                  color: INK,
                  background: isActive ? 'rgba(31,18,10,0.08)' : 'transparent',
                  border: 'none',
                  borderBottom: `1px solid ${RULE}`,
                  cursor: 'pointer',
                }}
              >
                <div>{p.name}</div>
                {p.isDefault && (
                  <div
                    style={{
                      fontFamily: "'Cormorant Garamond', serif",
                      fontStyle: 'italic',
                      fontSize: typeScale.micro,
                      color: INK_SOFT,
                      letterSpacing: 1.5,
                      textTransform: 'uppercase',
                    }}
                  >
                    Default
                  </div>
                )}
              </button>
            );
          })}
          <Link
            to="/profiles"
            onClick={() => setOpen(false)}
            style={{
              ...labelStyle,
              display: 'block',
              padding: `${space.xs} ${space.sm}`,
              borderBottom: `1px solid ${RULE}`,
              textDecoration: 'none',
            }}
          >
            Manage palates
          </Link>
          <button
            type="button"
            onClick={() => {
              logout();
              setOpen(false);
            }}
            style={{
              ...labelStyle,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              width: '100%',
              textAlign: 'left',
              padding: `${space.xs} ${space.sm}`,
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            <LogOut style={{ width: 14, height: 14 }} strokeWidth={1.5} />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
