'use client'

/**
 * OpenNowToggle - Pill-style toggle to filter dining halls by open status.
 * Active: green with dot indicator. Inactive: gray with dot indicator.
 */

interface OpenNowToggleProps {
  enabled: boolean
  onToggle: (enabled: boolean) => void
}

export function OpenNowToggle({ enabled, onToggle }: OpenNowToggleProps) {
  return (
    <button
      onClick={() => onToggle(!enabled)}
      className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer ${
        enabled
          ? 'bg-green-500 text-white'
          : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
      }`}
    >
      <span
        className={`inline-block h-2 w-2 rounded-full ${
          enabled ? 'bg-white' : 'bg-gray-400 dark:bg-gray-500'
        }`}
      />
      Open Now
    </button>
  )
}
