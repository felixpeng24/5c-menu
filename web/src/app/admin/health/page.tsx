"use client"

import { useEffect, useState } from "react"
import { fetchHealth, type ParserHealthResponse } from "@/lib/admin-api"

const HALL_DISPLAY: Record<string, string> = {
  hoch: "Hoch",
  collins: "Collins",
  malott: "Malott",
  mcconnell: "McConnell",
  frank: "Frank",
  frary: "Frary",
  oldenborg: "Oldenborg",
}

function timeAgo(isoString: string | null): string {
  if (!isoString) return "Never"
  const diff = Date.now() - new Date(isoString).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return "Just now"
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function statusColor(entry: ParserHealthResponse): {
  dot: string
  label: string
} {
  if (entry.total_runs_24h === 0) {
    return { dot: "bg-gray-400", label: "No data" }
  }
  if (entry.error_rate < 10) {
    return { dot: "bg-green-500", label: "Healthy" }
  }
  if (entry.error_rate < 30) {
    return { dot: "bg-yellow-500", label: "Degraded" }
  }
  return { dot: "bg-red-500", label: "Unhealthy" }
}

export default function HealthPage() {
  const [health, setHealth] = useState<ParserHealthResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadHealth = () => {
    setError(null)
    setLoading(true)
    fetchHealth()
      .then(setHealth)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadHealth()
  }, [])

  const healthyCount = health.filter(
    (h) => h.total_runs_24h > 0 && h.error_rate < 10
  ).length

  if (loading) {
    return <p className="text-gray-500">Loading parser health...</p>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Parser Health</h1>
        <button
          onClick={loadHealth}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded text-sm">
          {error}
        </div>
      )}

      {health.length === 0 ? (
        <p className="text-gray-500 text-sm">
          No parser data available. Parsers will appear here after their first execution.
        </p>
      ) : (
        <>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {healthyCount} of {health.length} parsers healthy
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {health.map((entry) => {
              const status = statusColor(entry)
              return (
                <div
                  key={entry.hall_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 shadow-sm"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <span
                      className={`inline-block w-3 h-3 rounded-full ${status.dot}`}
                    />
                    <h2 className="font-semibold">
                      {HALL_DISPLAY[entry.hall_id] ?? entry.hall_id}
                    </h2>
                    <span className="ml-auto text-xs text-gray-500">
                      {status.label}
                    </span>
                  </div>

                  <dl className="text-sm space-y-1">
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Last success</dt>
                      <dd>{timeAgo(entry.last_success)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Runs (24h)</dt>
                      <dd>{entry.total_runs_24h}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Errors (24h)</dt>
                      <dd>{entry.error_count_24h}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Error rate</dt>
                      <dd
                        className={
                          entry.error_rate >= 30
                            ? "text-red-600"
                            : entry.error_rate >= 10
                              ? "text-yellow-600"
                              : ""
                        }
                      >
                        {entry.error_rate.toFixed(1)}%
                      </dd>
                    </div>
                  </dl>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
