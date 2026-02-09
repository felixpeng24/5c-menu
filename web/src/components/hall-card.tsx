'use client'

import type { HallResponse } from '@/lib/types'
import { COLLEGE_BG } from '@/lib/constants'
import { Badge } from './ui/badge'
import { MealTabs } from './meal-tabs'

interface HallCardProps {
  hall: HallResponse
  date: string
  isOpen: boolean
  currentMeal?: string
}

export function HallCard({ hall, date, isOpen, currentMeal }: HallCardProps) {
  const bgClass = COLLEGE_BG[hall.college] ?? 'bg-gray-500'

  return (
    <div className={`${bgClass} rounded-2xl p-4 text-white dark:bg-opacity-90`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">{hall.name}</h2>
        <Badge variant={isOpen ? 'open' : 'closed'}>
          {isOpen ? 'Open' : 'Closed'}
        </Badge>
      </div>

      {/* Meal tabs and menu content */}
      <MealTabs hallId={hall.id} date={date} defaultMeal={currentMeal} />
    </div>
  )
}
