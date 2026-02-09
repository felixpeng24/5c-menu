import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DateBar } from '@/components/date-bar'

/** Get today in Pacific time as YYYY-MM-DD. */
function getPacificToday(): string {
  return new Date().toLocaleDateString('en-CA', {
    timeZone: 'America/Los_Angeles',
  })
}

describe('DateBar', () => {
  it('renders 7 date buttons', () => {
    const onDateChange = vi.fn()
    render(
      <DateBar selectedDate={getPacificToday()} onDateChange={onDateChange} />
    )
    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(7)
  })

  it('highlights selected date', () => {
    const today = getPacificToday()
    const onDateChange = vi.fn()
    render(<DateBar selectedDate={today} onDateChange={onDateChange} />)

    const todayButton = screen.getByText('Today')
    // Selected buttons have bg-gray-900 styling
    expect(todayButton.className).toContain('bg-gray-900')
  })

  it('calls onDateChange when a date is clicked', () => {
    const today = getPacificToday()
    const onDateChange = vi.fn()
    render(<DateBar selectedDate={today} onDateChange={onDateChange} />)

    // Click "Tomorrow" button (second date, not currently selected)
    const tomorrowButton = screen.getByText('Tomorrow')
    fireEvent.click(tomorrowButton)

    expect(onDateChange).toHaveBeenCalledTimes(1)
    // Should be called with a YYYY-MM-DD string
    expect(onDateChange.mock.calls[0][0]).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('shows "Today" label for first date', () => {
    const onDateChange = vi.fn()
    render(
      <DateBar selectedDate={getPacificToday()} onDateChange={onDateChange} />
    )
    expect(screen.getByText('Today')).toBeInTheDocument()
  })
})
