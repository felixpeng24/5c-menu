import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MenuItem } from '@/components/menu-item'

describe('MenuItem', () => {
  it('renders item name', () => {
    render(<MenuItem item={{ name: 'Grilled Chicken', tags: [] }} />)
    expect(screen.getByText('Grilled Chicken')).toBeInTheDocument()
  })

  it('renders dietary tag badges', () => {
    render(
      <MenuItem
        item={{ name: 'Tofu Bowl', tags: ['vegan', 'gluten-free'] }}
      />
    )
    expect(screen.getByText('V')).toBeInTheDocument()
    expect(screen.getByText('GF')).toBeInTheDocument()
  })

  it('ignores unknown tags', () => {
    render(
      <MenuItem item={{ name: 'Mystery Meat', tags: ['unknown-tag'] }} />
    )
    expect(screen.getByText('Mystery Meat')).toBeInTheDocument()
    // The unknown tag should not produce any badge. Only known tags from
    // DIETARY_ICONS produce badges (V, VG, GF, N, HL).
    const badges = ['V', 'VG', 'GF', 'N', 'HL']
    badges.forEach((badge) => {
      expect(screen.queryByText(badge)).not.toBeInTheDocument()
    })
  })
})
