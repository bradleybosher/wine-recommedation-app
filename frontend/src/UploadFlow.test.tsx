import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import UploadFlow from '@/UploadFlow'

// Stub the heavy child screens so the test focuses on UploadFlow's pathway switch.
vi.mock('@/UploadCellarInventoryScreen', () => ({
  default: () => <div>cellar-inventory-screen</div>,
}))
vi.mock('@/UploadTastingHistoryScreen', () => ({
  default: () => <div>tasting-history-screen</div>,
}))
vi.mock('@/SeedBottlesScreen', () => ({
  default: () => <div>seed-bottles-screen</div>,
}))

describe('UploadFlow', () => {
  it('starts at the pathway-chooser', () => {
    render(<UploadFlow onComplete={() => {}} />)
    expect(screen.getByText(/i use cellartracker/i)).toBeInTheDocument()
    expect(screen.getByText(/name a few wines i love/i)).toBeInTheDocument()
  })

  it('navigates to the cellartracker pathway and shows the inventory screen first', async () => {
    render(<UploadFlow onComplete={() => {}} />)
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /i use cellartracker/i }))
    })
    expect(screen.getByText('cellar-inventory-screen')).toBeInTheDocument()
  })

  it('navigates to the seed pathway and shows the seed-bottles screen', async () => {
    render(<UploadFlow onComplete={() => {}} />)
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /name a few wines i love/i }))
    })
    expect(screen.getByText('seed-bottles-screen')).toBeInTheDocument()
  })

  it('lets the user switch pathways via the back button', async () => {
    render(<UploadFlow onComplete={() => {}} />)
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /name a few wines i love/i }))
    })
    expect(screen.getByText('seed-bottles-screen')).toBeInTheDocument()
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: /change pathway/i }))
    })
    // Back at chooser
    expect(screen.getByText(/i use cellartracker/i)).toBeInTheDocument()
  })
})
