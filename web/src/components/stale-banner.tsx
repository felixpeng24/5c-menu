'use client'

/**
 * StaleBanner - Amber banner indicating data freshness.
 * Uses Intl.RelativeTimeFormat for relative time display (no external deps).
 * Only renders when data is stale.
 */

interface StaleBannerProps {
  fetchedAt: string | null
  isStale: boolean
}

/** Format an ISO timestamp as a relative time string (e.g. "5 minutes ago"). */
function timeAgo(isoString: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(isoString).getTime()) / 1000
  )
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

  if (seconds < 60) return rtf.format(-seconds, 'second')
  if (seconds < 3600) return rtf.format(-Math.floor(seconds / 60), 'minute')
  if (seconds < 86400) return rtf.format(-Math.floor(seconds / 3600), 'hour')
  return rtf.format(-Math.floor(seconds / 86400), 'day')
}

export function StaleBanner({ fetchedAt, isStale }: StaleBannerProps) {
  if (!isStale || !fetchedAt) return null

  return (
    <div className="flex items-center gap-2 bg-amber-50 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 text-xs px-3 py-1.5 rounded-lg">
      <svg
        className="h-3.5 w-3.5 shrink-0"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.168 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 6a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 6zm0 9a1 1 0 100-2 1 1 0 000 2z"
          clipRule="evenodd"
        />
      </svg>
      <span>Last updated {timeAgo(fetchedAt)}</span>
    </div>
  )
}
