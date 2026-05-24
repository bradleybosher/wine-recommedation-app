import { describe, expect, it, vi, beforeEach } from 'vitest'

import {
  ACTIVE_PROFILE_STORAGE_KEY,
  TOKEN_STORAGE_KEY,
  readActiveProfileId,
  readToken,
  setUnauthorizedHandler,
} from '@/client/configure'

describe('configure storage readers', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('readToken returns null when not set', () => {
    expect(readToken()).toBeNull()
  })

  it('readToken returns persisted token', () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, 'tok-123')
    expect(readToken()).toBe('tok-123')
  })

  it('readActiveProfileId returns persisted profile id', () => {
    localStorage.setItem(ACTIVE_PROFILE_STORAGE_KEY, 'pid-456')
    expect(readActiveProfileId()).toBe('pid-456')
  })

  it('readers swallow localStorage errors and return null', () => {
    const original = Storage.prototype.getItem
    Storage.prototype.getItem = () => {
      throw new Error('quota')
    }
    try {
      expect(readToken()).toBeNull()
      expect(readActiveProfileId()).toBeNull()
    } finally {
      Storage.prototype.getItem = original
    }
  })
})

describe('setUnauthorizedHandler', () => {
  it('accepts a handler and null without throwing', () => {
    const handler = vi.fn()
    expect(() => setUnauthorizedHandler(handler)).not.toThrow()
    expect(() => setUnauthorizedHandler(null)).not.toThrow()
  })
})
