import { useState, type FormEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import { INK_SOFT, OXBLOOD, space, typeScale } from '@/design/tokens';
import { errorStyle, inputStyle, labelStyle, primaryBtn } from '@/design/forms';
import { resetPasswordAuthResetPasswordPost } from '@/client/sdk.gen';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';

  const [newPassword, setNewPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (newPassword !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      await resetPasswordAuthResetPasswordPost({ body: { token, newPassword } });
      setDone(true);
    } catch (err: any) {
      setError(extractErrorMessage(err) ?? 'Something went wrong. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <PaperFrame>
      <Masthead />
      <RuleDouble />
      <div style={{ maxWidth: 440, margin: `${space.xl} auto`, padding: `0 ${space.md}` }}>
        <h1
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.h2,
            marginBottom: space.sm,
          }}
        >
          Choose a new password
        </h1>

        {!token ? (
          <p
            style={{
              fontFamily: "'EB Garamond', serif",
              fontSize: typeScale.body,
              color: OXBLOOD,
              marginBottom: space.lg,
            }}
          >
            Invalid or missing reset link.{' '}
            <Link to="/forgot-password" style={{ color: OXBLOOD }}>
              Request a new one.
            </Link>
          </p>
        ) : done ? (
          <>
            <p
              style={{
                fontFamily: "'EB Garamond', serif",
                fontSize: typeScale.body,
                lineHeight: 1.6,
                marginBottom: space.lg,
              }}
            >
              Password updated.
            </p>
            <Link
              to="/login"
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: typeScale.body,
                color: OXBLOOD,
              }}
            >
              Sign in
            </Link>
          </>
        ) : (
          <>
            <p
              style={{
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: typeScale.body,
                color: INK_SOFT,
                marginBottom: space.lg,
              }}
            >
              Enter a new password for your account.
            </p>

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: space.md }}>
                <label style={labelStyle} htmlFor="reset-password">New password</label>
                <input
                  id="reset-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  style={inputStyle}
                />
                <p
                  style={{
                    fontFamily: "'EB Garamond', serif",
                    fontSize: typeScale.label,
                    color: INK_SOFT,
                    marginTop: 4,
                  }}
                >
                  At least 8 characters.
                </p>
              </div>

              <div style={{ marginBottom: space.lg }}>
                <label style={labelStyle} htmlFor="reset-confirm">Confirm password</label>
                <input
                  id="reset-confirm"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  style={inputStyle}
                />
              </div>

              {error && (
                <div style={{ ...errorStyle, marginBottom: space.md, color: OXBLOOD }}>{error}</div>
              )}

              <button
                type="submit"
                disabled={busy}
                style={{ ...primaryBtn, width: '100%', opacity: busy ? 0.6 : 1 }}
              >
                {busy ? (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <Loader2 className="animate-spin" style={{ width: 14, height: 14 }} strokeWidth={1.5} />
                    Updating
                  </span>
                ) : (
                  'Set new password'
                )}
              </button>
            </form>
          </>
        )}
      </div>
    </PaperFrame>
  );
}

function extractErrorMessage(err: any): string | null {
  if (!err) return null;
  if (typeof err === 'string') return err;
  const detail = err?.body?.detail ?? err?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return err?.message ?? null;
}
