import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { OpenNowToggle } from '@/components/open-now-toggle'

describe('OpenNowToggle', () => {
  it('renders with "Open Now" text', () => {
    render(<OpenNowToggle enabled={false} onToggle={vi.fn()} />)
    expect(screen.getByText('Open Now')).toBeInTheDocument()
  })

  it('calls onToggle with true when clicked while disabled', () => {
    const onToggle = vi.fn()
    render(<OpenNowToggle enabled={false} onToggle={onToggle} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onToggle).toHaveBeenCalledWith(true)
  })

  it('calls onToggle with false when clicked while enabled', () => {
    const onToggle = vi.fn()
    render(<OpenNowToggle enabled={true} onToggle={onToggle} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onToggle).toHaveBeenCalledWith(false)
  })
})
