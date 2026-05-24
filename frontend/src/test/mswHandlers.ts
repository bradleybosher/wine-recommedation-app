import { http, HttpResponse } from 'msw'

const API = 'http://localhost'

/**
 * Default handlers — minimal happy-path stubs.
 * Individual tests should call `server.use(...)` to override per-case.
 */
export const handlers = [
  http.post(`${API}/auth/login`, async () =>
    HttpResponse.json({
      accessToken: 'test-token',
      tokenType: 'bearer',
      user: { id: 'user-1', email: 'test@example.com', createdAt: 0 },
      profile: { id: 'profile-1', name: 'Default', userId: 'user-1', isDefault: true, createdAt: 0 },
    }),
  ),

  http.post(`${API}/auth/register`, async () =>
    HttpResponse.json({
      accessToken: 'test-token',
      tokenType: 'bearer',
      user: { id: 'user-1', email: 'test@example.com', createdAt: 0 },
      profile: { id: 'profile-1', name: 'Default', userId: 'user-1', isDefault: true, createdAt: 0 },
    }),
  ),

  http.get(`${API}/auth/me`, () =>
    HttpResponse.json({
      user: { id: 'user-1', email: 'test@example.com', createdAt: 0 },
      profiles: [{ id: 'profile-1', name: 'Default', userId: 'user-1', isDefault: true, createdAt: 0 }],
    }),
  ),

  http.get(`${API}/profiles`, () =>
    HttpResponse.json([
      { id: 'profile-1', name: 'Default', userId: 'user-1', isDefault: true, createdAt: 0 },
    ]),
  ),
]
