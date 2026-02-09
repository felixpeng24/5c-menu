'use client'

/**
 * DateBar - 7-day horizontal date navigation for menu browsing.
 * All "today" computations use Pacific time since the Claremont Colleges
 * are in California. A user in EST after midnight PST should still see
 * the correct Pacific "today".
 */

interface DateBarProps {
  selectedDate: string // YYYY-MM-DD
  onDateChange: (date: string) => void
}

/** Return today's date string (YYYY-MM-DD) in Pacific time. */
function getPacificToday(): string {
  return new Date().toLocaleDateString('en-CA', {
    timeZone: 'America/Los_Angeles',
  })
}

/** Generate 7 Date objects starting from Pacific today. */
function getDateRange(pacificToday: string): Date[] {
  const base = new Date(pacificToday + 'T12:00:00') // noon to avoid DST edge
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(base)
    d.setDate(base.getDate() + i)
    return d
  })
}

/** Convert a Date to YYYY-MM-DD. Safe because dates are constructed at noon UTC. */
function toDateString(date: Date): string {
  return date.toISOString().slice(0, 10)
}

/** Label: "Today", "Tomorrow", or short format like "Mon, Feb 10". */
function formatDateLabel(date: Date, pacificToday: string): string {
  const dateStr = toDateString(date)
  if (dateStr === pacificToday) return 'Today'

  const tomorrow = new Date(pacificToday + 'T12:00:00')
  tomorrow.setDate(tomorrow.getDate() + 1)
  if (dateStr === toDateString(tomorrow)) return 'Tomorrow'

  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}

export function DateBar({ selectedDate, onDateChange }: DateBarProps) {
  const pacificToday = getPacificToday()
  const dates = getDateRange(pacificToday)

  return (
    <div className="no-scrollbar flex gap-2 overflow-x-auto py-2 px-1">
      {dates.map((date) => {
        const dateStr = toDateString(date)
        const isSelected = dateStr === selectedDate
        return (
          <button
            key={dateStr}
            onClick={() => onDateChange(dateStr)}
            className={`shrink-0 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isSelected
                ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
            }`}
          >
            {formatDateLabel(date, pacificToday)}
          </button>
        )
      })}
    </div>
  )
}
