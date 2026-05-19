import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import { INK_SOFT, OXBLOOD, space, typeScale } from '@/design/tokens';
import {
  errorStyle,
  helperStyle,
  inputStyle,
  labelStyle,
  primaryBtn,
} from '@/design/forms';
import { useAuth } from '@/state/authStore';

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const validate = (): string | null => {
    if (password.length < 8) return 'Password must be at least 8 characters.';
    if (password !== confirm) return 'Passwords do not match.';
    return null;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const failure = validate();
    if (failure) {
      setError(failure);
      return;
    }
    setError(null);
    setBusy(true);
    try {
      await register(email.trim(), password);
      navigate('/', { replace: true });
    } catch (err: any) {
      setError(extractErrorMessage(err) ?? 'Could not create account. Try a different email.');
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
          Create an account
        </h1>
        <p
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.body,
            color: INK_SOFT,
            marginBottom: space.lg,
          }}
        >
          The first account claims any existing palate already on this server.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: space.md }}>
            <label style={labelStyle} htmlFor="register-email">Email</label>
            <input
              id="register-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: space.md }}>
            <label style={labelStyle} htmlFor="register-password">Password</label>
            <input
              id="register-password"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={inputStyle}
            />
            <div style={helperStyle}>At least 8 characters.</div>
          </div>

          <div style={{ marginBottom: space.lg }}>
            <label style={labelStyle} htmlFor="register-confirm">Confirm password</label>
            <input
              id="register-confirm"
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

          <button type="submit" disabled={busy} style={{ ...primaryBtn, width: '100%', opacity: busy ? 0.6 : 1 }}>
            {busy ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                <Loader2 className="animate-spin" style={{ width: 14, height: 14 }} strokeWidth={1.5} />
                Creating account
              </span>
            ) : (
              'Begin'
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
          Already have an account?{' '}
          <Link to="/login" style={{ color: OXBLOOD }}>
            Sign in
          </Link>
        </div>
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
