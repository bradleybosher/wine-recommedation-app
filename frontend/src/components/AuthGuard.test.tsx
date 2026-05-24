import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import AuthGuard from '@/components/AuthGuard'

// Mock the auth store so we can drive AuthGuard's status branches deterministically.
const mockStatus = vi.hoisted(() => ({ value: 'loading' as 'loading' | 'unauthenticated' | 'authenticated' }))
vi.mock('@/state/authStore', () => ({
  useAuth: () => ({ status: mockStatus.value }),
}))

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/protected"
          element={
            <AuthGuard>
              <div>secret content</div>
            </AuthGuard>
          }
        />
        <Route path="/login" element={<div>login page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AuthGuard', () => {
  it('renders loading state when status=loading', () => {
    mockStatus.value = 'loading'
    renderAt('/protected')
    expect(screen.getByText(/verifying credentials/i)).toBeInTheDocument()
    expect(screen.queryByText(/secret content/)).not.toBeInTheDocument()
  })

  it('redirects to /login when unauthenticated', () => {
    mockStatus.value = 'unauthenticated'
    renderAt('/protected')
    expect(screen.getByText(/login page/)).toBeInTheDocument()
    expect(screen.queryByText(/secret content/)).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    mockStatus.value = 'authenticated'
    renderAt('/protected')
    expect(screen.getByText(/secret content/)).toBeInTheDocument()
  })
})
