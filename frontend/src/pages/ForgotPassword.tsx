import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import { INK_SOFT, OXBLOOD, space, typeScale } from '@/design/tokens';
import { errorStyle, inputStyle, labelStyle, primaryBtn } from '@/design/forms';
import { forgotPasswordAuthForgotPasswordPost } from '@/client/sdk.gen';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await forgotPasswordAuthForgotPasswordPost({ body: { email: email.trim() } });
      setSent(true);
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
          Reset password
        </h1>

        {sent ? (
          <>
            <p
              style={{
                fontFamily: "'EB Garamond', serif",
                fontSize: typeScale.body,
                lineHeight: 1.6,
                marginBottom: space.lg,
              }}
            >
              If that address is registered, a reset link has been logged to the server console.
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
              Back to sign in
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
              Enter your email and a reset link will be logged to the server console.
            </p>

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: space.lg }}>
                <label style={labelStyle} htmlFor="forgot-email">Email</label>
                <input
                  id="forgot-email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
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
                    Sending
                  </span>
                ) : (
                  'Send reset link'
                )}
              </button>
            </form>

            <div
              style={{
                marginTop: space.lg,
                fontFamily: "'EB Garamond', serif",
                fontStyle: 'italic',
                fontSize: typeScale.body,
                color: INK_SOFT,
              }}
            >
              Remembered it?{' '}
              <Link to="/login" style={{ color: OXBLOOD }}>
                Back to sign in
              </Link>
            </div>
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
