'use client'

import type { StationResponse } from '@/lib/types'
import { MenuItem } from './menu-item'

interface StationListProps {
  stations: StationResponse[]
}

export function StationList({ stations }: StationListProps) {
  if (stations.length === 0) {
    return (
      <p className="text-white/60 text-sm py-2">No menu items available</p>
    )
  }

  return (
    <div className="space-y-3">
      {stations.map((station) => (
        <div key={station.name}>
          <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-1">
            {station.name}
          </h3>
          <div className="space-y-0.5">
            {station.items.map((item) => (
              <MenuItem key={item.name} item={item} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
