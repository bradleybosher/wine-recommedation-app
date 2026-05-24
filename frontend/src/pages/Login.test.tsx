import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import Login from '@/pages/Login'
import { AuthProvider } from '@/state/authStore'
import { server } from '@/test/setup'

function renderLogin(initialPath = '/login', from?: string) {
  const entries = from ? [{ pathname: initialPath, state: { from } }] : [initialPath]
  return render(
    <MemoryRouter initialEntries={entries as any}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<div>home page</div>} />
          <Route path="/secret" element={<div>secret page</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('Login page', () => {
  it('shows the sign-in heading and email/password inputs', () => {
    renderLogin()
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('redirects to / after successful login', async () => {
    renderLogin()
    await userEvent.type(screen.getByLabelText(/email/i), 'alice@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'longpassword')
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /enter/i }))
    })
    await waitFor(() => expect(screen.getByText(/home page/)).toBeInTheDocument())
  })

  it('redirects to the `from` path when provided in location state', async () => {
    renderLogin('/login', '/secret')
    await userEvent.type(screen.getByLabelText(/email/i), 'alice@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'longpassword')
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /enter/i }))
    })
    await waitFor(() => expect(screen.getByText(/secret page/)).toBeInTheDocument())
  })

  it('surfaces a failure message when the server returns 401', async () => {
    // NOTE: the SDK routes non-2xx payloads to response.error, leaving response.data
    // undefined. authStore throws "Login failed: no response payload" in that case
    // and the page falls back to its generic "Sign in failed" copy. This test
    // pins that user-visible behaviour (not the raw server detail).
    server.use(
      http.post('http://localhost/auth/login', () =>
        HttpResponse.json({ detail: 'Invalid email or password' }, { status: 401 }),
      ),
    )
    renderLogin()
    await userEvent.type(screen.getByLabelText(/email/i), 'alice@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'wrong')
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /enter/i }))
    })
    await waitFor(() =>
      expect(
        screen.getByText(/sign in failed|login failed|no response payload/i),
      ).toBeInTheDocument(),
    )
  })

  it('still surfaces a failure message on 422 validation errors', async () => {
    server.use(
      http.post('http://localhost/auth/login', () =>
        HttpResponse.json(
          { detail: [{ msg: 'String too short', type: 'value_error' }] },
          { status: 422 },
        ),
      ),
    )
    renderLogin()
    await userEvent.type(screen.getByLabelText(/email/i), 'alice@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'x')
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /enter/i }))
    })
    await waitFor(() =>
      expect(
        screen.getByText(/sign in failed|login failed|no response payload|string too short/i),
      ).toBeInTheDocument(),
    )
  })
})
