import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StaleBanner } from '@/components/stale-banner'

describe('StaleBanner', () => {
  it('renders nothing when isStale is false', () => {
    const { container } = render(
      <StaleBanner isStale={false} fetchedAt="2026-01-01T00:00:00Z" />
    )
    expect(container.innerHTML).toBe('')
  })

  it('renders nothing when fetchedAt is null', () => {
    const { container } = render(
      <StaleBanner isStale={true} fetchedAt={null} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('shows "Last updated" text when stale with valid fetchedAt', () => {
    const oneHourAgo = new Date(Date.now() - 3600 * 1000).toISOString()
    render(<StaleBanner isStale={true} fetchedAt={oneHourAgo} />)
    expect(screen.getByText(/last updated/i)).toBeInTheDocument()
  })
})
