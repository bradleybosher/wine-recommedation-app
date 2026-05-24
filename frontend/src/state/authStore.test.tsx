import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'

import { AuthProvider, useAuth } from '@/state/authStore'
import { TOKEN_STORAGE_KEY } from '@/client/configure'
import { server } from '@/test/setup'

function Probe() {
  const { status, user, login, logout, register } = useAuth()
  return (
    <div>
      <div data-testid="status">{status}</div>
      <div data-testid="email">{user?.email ?? '(none)'}</div>
      <button onClick={() => login('alice@example.com', 'longpassword')}>login</button>
      <button onClick={() => register('alice@example.com', 'longpassword')}>register</button>
      <button onClick={logout}>logout</button>
    </div>
  )
}

function renderProbe() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )
}

describe('AuthProvider', () => {
  it('starts unauthenticated when localStorage is empty', () => {
    renderProbe()
    expect(screen.getByTestId('status').textContent).toBe('unauthenticated')
    expect(screen.getByTestId('email').textContent).toBe('(none)')
  })

  it('persists token to localStorage on login', async () => {
    renderProbe()
    await act(async () => {
      await userEvent.click(screen.getByText('login'))
    })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('authenticated'))
    expect(screen.getByTestId('email').textContent).toBe('test@example.com')
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBe('test-token')
  })

  it('clears token and resets state on logout', async () => {
    renderProbe()
    await act(async () => {
      await userEvent.click(screen.getByText('login'))
    })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('authenticated'))

    await act(async () => {
      await userEvent.click(screen.getByText('logout'))
    })
    expect(screen.getByTestId('status').textContent).toBe('unauthenticated')
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
  })

  it('supports the register flow returning the same shape', async () => {
    renderProbe()
    await act(async () => {
      await userEvent.click(screen.getByText('register'))
    })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('authenticated'))
    expect(screen.getByTestId('email').textContent).toBe('test@example.com')
  })

  it('logs the user out when the server returns 401', async () => {
    // Pre-seed an authenticated session
    localStorage.setItem(TOKEN_STORAGE_KEY, 'pre-existing')
    localStorage.setItem(
      'vinotheque.user',
      JSON.stringify({ id: 'u1', email: 'old@example.com', createdAt: 0 }),
    )

    // Make /auth/me return 401 → AuthProvider's loading→refreshUser path should call logout
    server.use(
      http.get('http://localhost/auth/me', () => new HttpResponse(null, { status: 401 })),
    )

    renderProbe()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('unauthenticated'))
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
  })
})
