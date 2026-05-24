import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import FileUploader from '@/FileUploader'

function setup(initialFile: File | null = null) {
  const onFileChange = vi.fn()
  render(
    <FileUploader
      onFileChange={onFileChange}
      file={initialFile}
      previewUrl=""
      error=""
    />,
  )
  return { onFileChange }
}

describe('FileUploader', () => {
  it('rejects file with disallowed MIME type', async () => {
    const { onFileChange } = setup()
    const input = document.getElementById('wine-file-upload') as HTMLInputElement
    const badFile = new File(['x'], 'malware.exe', { type: 'application/x-msdownload' })
    fireEvent.change(input, { target: { files: [badFile] } })
    await waitFor(() => expect(onFileChange).toHaveBeenCalled())
    const [file, , , errorMsg] = onFileChange.mock.calls[0]
    expect(file).toBeNull()
    expect(errorMsg).toMatch(/invalid file type/i)
  })

  it('rejects file larger than 10 MB', async () => {
    const { onFileChange } = setup()
    const input = document.getElementById('wine-file-upload') as HTMLInputElement
    // 10 MB + 1 byte
    const big = new File([new Uint8Array(10 * 1024 * 1024 + 1)], 'big.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [big] } })
    await waitFor(() => expect(onFileChange).toHaveBeenCalled())
    const [file, , , errorMsg] = onFileChange.mock.calls[0]
    expect(file).toBeNull()
    expect(errorMsg).toMatch(/too large/i)
  })

  it('reads valid PDF as base64 and reports it via callback', async () => {
    const { onFileChange } = setup()
    const input = document.getElementById('wine-file-upload') as HTMLInputElement
    const pdf = new File(['%PDF-1.4'], 'list.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [pdf] } })
    await waitFor(() => expect(onFileChange).toHaveBeenCalled())
    const [file, previewUrl, base64, errorMsg] = onFileChange.mock.calls[0]
    expect(file).toBe(pdf)
    expect(errorMsg).toBe('')
    expect(previewUrl).toMatch(/^data:application\/pdf;base64,/)
    expect(base64.length).toBeGreaterThan(0)
  })

  it('handles a drop event with a valid image', async () => {
    const { onFileChange } = setup()
    const dropZone = screen.getByText(/drop a file here/i).closest('div')!.parentElement!
    const img = new File([new Uint8Array([1, 2, 3])], 'shot.png', { type: 'image/png' })
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [img], dropEffect: 'copy' },
    })
    await waitFor(() => expect(onFileChange).toHaveBeenCalled())
    const [file] = onFileChange.mock.calls[0]
    expect(file).toBe(img)
  })
})
