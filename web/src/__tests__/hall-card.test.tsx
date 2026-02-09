import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { HallCard } from '@/components/hall-card'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the useMenu hook to avoid real API calls in tests
vi.mock('@/lib/hooks', () => ({
  useMenu: () => ({
    data: undefined,
    isLoading: false,
    error: null,
  }),
}))

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

const mockHall = {
  id: 'collins',
  name: 'Collins',
  college: 'cmc',
  vendor_type: 'bonappetit',
  color: '#800000',
}

describe('HallCard', () => {
  it('renders hall name', () => {
    renderWithQuery(
      <HallCard hall={mockHall} date="2026-02-09" isOpen={true} />
    )
    expect(screen.getByText('Collins')).toBeInTheDocument()
  })

  it('shows Open badge when hall is open', () => {
    renderWithQuery(
      <HallCard hall={mockHall} date="2026-02-09" isOpen={true} />
    )
    expect(screen.getByText('Open')).toBeInTheDocument()
  })

  it('shows Closed badge when hall is closed', () => {
    renderWithQuery(
      <HallCard hall={mockHall} date="2026-02-09" isOpen={false} />
    )
    expect(screen.getByText('Closed')).toBeInTheDocument()
  })

  it('renders meal tabs', () => {
    renderWithQuery(
      <HallCard hall={mockHall} date="2026-02-09" isOpen={true} />
    )
    // MealTabs renders tab buttons for available meals.
    // Collins (cmc) has breakfast, lunch, dinner.
    expect(screen.getByText('Breakfast')).toBeInTheDocument()
    expect(screen.getByText('Lunch')).toBeInTheDocument()
    expect(screen.getByText('Dinner')).toBeInTheDocument()
  })
})
