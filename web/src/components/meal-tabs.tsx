'use client'

import { useState } from 'react'
import { useMenu } from '@/lib/hooks'
import { HALL_MEALS, DEFAULT_MEAL } from '@/lib/constants'
import { StationList } from './station-list'
import { Skeleton } from './ui/skeleton'

interface MealTabsProps {
  hallId: string
  date: string
  defaultMeal?: string
}

export function MealTabs({ hallId, date, defaultMeal }: MealTabsProps) {
  const availableMeals = HALL_MEALS[hallId] ?? ['breakfast', 'lunch', 'dinner']

  const initialMeal =
    defaultMeal && availableMeals.includes(defaultMeal)
      ? defaultMeal
      : availableMeals[0] ?? DEFAULT_MEAL

  const [selectedMeal, setSelectedMeal] = useState(initialMeal)

  const { data, isLoading, error } = useMenu(hallId, date, selectedMeal)

  return (
    <div className="mt-3">
      {/* Tab bar */}
      <div className="flex gap-1 mb-3">
        {availableMeals.map((meal) => (
          <button
            key={meal}
            onClick={() => setSelectedMeal(meal)}
            className={`rounded-full px-3 py-1 text-sm transition-colors ${
              meal === selectedMeal
                ? 'bg-white/20 text-white font-bold'
                : 'text-white/70 hover:text-white'
            }`}
          >
            {meal.charAt(0).toUpperCase() + meal.slice(1)}
          </button>
        ))}
      </div>

      {/* Stale data indicator */}
      {data?.is_stale && data.fetched_at && (
        <p className="text-amber-300 text-xs mb-2">Data may be outdated</p>
      )}

      {/* Content */}
      {isLoading && (
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-3/4" />
          <Skeleton className="h-4 w-20 mt-2" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-5/6" />
        </div>
      )}

      {error && (
        <p className="text-red-300 text-sm">
          Failed to load menu. Please try again.
        </p>
      )}

      {data && !isLoading && <StationList stations={data.stations} />}
    </div>
  )
}
