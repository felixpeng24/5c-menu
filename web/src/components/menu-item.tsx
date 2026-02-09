'use client'

import type { MenuItemResponse } from '@/lib/types'
import { DIETARY_ICONS } from '@/lib/constants'

interface MenuItemProps {
  item: MenuItemResponse
}

export function MenuItem({ item }: MenuItemProps) {
  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-white/80 text-sm">{item.name}</span>
      <div className="flex gap-1 ml-2 shrink-0">
        {item.tags.map((tag) => {
          const label = DIETARY_ICONS[tag]
          if (!label) return null
          return (
            <span
              key={tag}
              className="rounded-full bg-white/20 px-1.5 py-0.5 text-[10px] font-semibold text-white/90"
            >
              {label}
            </span>
          )
        })}
      </div>
    </div>
  )
}
