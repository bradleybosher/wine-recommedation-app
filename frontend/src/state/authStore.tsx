import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import {
  loginAuthLoginPost,
  meAuthMeGet,
  registerAuthRegisterPost,
} from '@/client';
import type { Profile, User } from '@/client/types.gen';
import {
  ACTIVE_PROFILE_STORAGE_KEY,
  TOKEN_STORAGE_KEY,
  installAuthInterceptors,
  readActiveProfileId,
  readToken,
  setUnauthorizedHandler,
} from '@/client/configure';

const USER_STORAGE_KEY = 'vinotheque.user';

interface AuthState {
  status: 'loading' | 'unauthenticated' | 'authenticated';
  user: User | null;
  token: string | null;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<{ user: User; profile: Profile }>;
  register: (email: string, password: string) => Promise<{ user: User; profile: Profile }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

function persist(token: string | null, user: User | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else localStorage.removeItem(TOKEN_STORAGE_KEY);
    if (user) localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    else localStorage.removeItem(USER_STORAGE_KEY);
  } catch {
    /* ignore storage errors */
  }
}

installAuthInterceptors();

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(() => {
    const token = readToken();
    const user = readStoredUser();
    return token && user
      ? { status: 'loading', user, token }
      : { status: 'unauthenticated', user: null, token: null };
  });

  const logout = useCallback(() => {
    persist(null, null);
    try {
      localStorage.removeItem(ACTIVE_PROFILE_STORAGE_KEY);
    } catch {
      /* ignore */
    }
    setState({ status: 'unauthenticated', user: null, token: null });
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout();
    });
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  const refreshUser = useCallback(async () => {
    const token = readToken();
    if (!token) {
      setState({ status: 'unauthenticated', user: null, token: null });
      return;
    }
    try {
      const response = await meAuthMeGet();
      const user = response.data?.user;
      if (user) {
        persist(token, user);
        setState({ status: 'authenticated', user, token });
      } else {
        logout();
      }
    } catch {
      logout();
    }
  }, [logout]);

  useEffect(() => {
    if (state.status === 'loading') {
      refreshUser();
    }
  }, [state.status, refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginAuthLoginPost({ body: { email, password } });
    const data = response.data;
    if (!data) {
      throw new Error('Login failed: no response payload');
    }
    persist(data.accessToken, data.user);
    setState({ status: 'authenticated', user: data.user, token: data.accessToken });
    return { user: data.user, profile: data.profile };
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const response = await registerAuthRegisterPost({ body: { email, password } });
    const data = response.data;
    if (!data) {
      throw new Error('Registration failed: no response payload');
    }
    persist(data.accessToken, data.user);
    setState({ status: 'authenticated', user: data.user, token: data.accessToken });
    return { user: data.user, profile: data.profile };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, login, register, logout, refreshUser }),
    [state, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
