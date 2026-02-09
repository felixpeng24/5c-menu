'use client'

import { useState, useMemo } from 'react'
import { useHalls, useOpenNow } from '@/lib/hooks'
import { HallCard } from '@/components/hall-card'
import { DateBar } from '@/components/date-bar'
import { OpenNowToggle } from '@/components/open-now-toggle'
import { Skeleton } from '@/components/ui/skeleton'

/** Return today's date string (YYYY-MM-DD) in Pacific time. */
function getPacificToday(): string {
  return new Date().toLocaleDateString('en-CA', {
    timeZone: 'America/Los_Angeles',
  })
}

export default function Home() {
  const [selectedDate, setSelectedDate] = useState(getPacificToday)
  const [openNowFilter, setOpenNowFilter] = useState(false)

  const { data: halls, isLoading, error, refetch } = useHalls()
  const { data: openNowData } = useOpenNow()

  const isToday = selectedDate === getPacificToday()

  const openHallIds = useMemo(
    () => new Set(openNowData?.map((h) => h.id) ?? []),
    [openNowData]
  )

  const openHallMeals = useMemo(
    () =>
      new Map(openNowData?.map((h) => [h.id, h.current_meal]) ?? []),
    [openNowData]
  )

  const filteredHalls = useMemo(() => {
    if (!halls) return []
    if (openNowFilter && isToday) {
      return halls.filter((hall) => openHallIds.has(hall.id))
    }
    return halls
  }, [halls, openNowFilter, isToday, openHallIds])

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-gray-50/80 dark:bg-gray-950/80 backdrop-blur-sm px-4 pt-4 pb-2">
        <div className="max-w-lg mx-auto">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              5C Menu
            </h1>
            <OpenNowToggle enabled={openNowFilter} onToggle={setOpenNowFilter} />
          </div>
          <DateBar selectedDate={selectedDate} onDateChange={setSelectedDate} />
        </div>
      </header>

      {/* Hall feed */}
      <div className="max-w-lg mx-auto px-4 pb-4 space-y-4">
        {/* Open Now note when filter active on non-today date */}
        {openNowFilter && !isToday && (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-1">
            Open Now filter only applies to today
          </p>
        )}

        {/* Loading skeletons */}
        {isLoading && (
          <div className="space-y-4">
            {Array.from({ length: 4 }, (_, i) => (
              <Skeleton key={i} className="h-48 w-full rounded-2xl" />
            ))}
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="text-red-600 dark:text-red-400 text-sm mb-3">
              Failed to load dining halls.
            </p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-lg text-sm font-medium"
            >
              Retry
            </button>
          </div>
        )}

        {/* Hall cards */}
        {filteredHalls.map((hall) => (
          <HallCard
            key={hall.id}
            hall={hall}
            date={selectedDate}
            isOpen={openHallIds.has(hall.id)}
            currentMeal={openHallMeals.get(hall.id)}
          />
        ))}

        {/* Empty state */}
        {filteredHalls.length === 0 && !isLoading && !error && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-gray-500 dark:text-gray-400 text-sm mb-2">
              No dining halls are currently open.
            </p>
            <button
              onClick={() => setOpenNowFilter(false)}
              className="text-sm text-blue-600 dark:text-blue-400 underline"
            >
              Show all halls
            </button>
          </div>
        )}
      </div>
    </main>
  )
}
