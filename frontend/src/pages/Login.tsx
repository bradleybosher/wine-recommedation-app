import { useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import { INK_SOFT, OXBLOOD, space, typeScale } from '@/design/tokens';
import {
  errorStyle,
  inputStyle,
  labelStyle,
  primaryBtn,
} from '@/design/forms';
import { useAuth } from '@/state/authStore';

interface LocationState {
  from?: string;
}

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email.trim(), password);
      const from = (location.state as LocationState | null)?.from ?? '/';
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(extractErrorMessage(err) ?? 'Sign in failed. Check your email and password.');
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
          Sign in
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
          Resume the conversation between your palate and the cellar.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: space.md }}>
            <label style={labelStyle} htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: space.lg }}>
            <label style={labelStyle} htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
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
                Signing in
              </span>
            ) : (
              'Enter'
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
          New here?{' '}
          <Link to="/register" style={{ color: OXBLOOD }}>
            Create an account
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
