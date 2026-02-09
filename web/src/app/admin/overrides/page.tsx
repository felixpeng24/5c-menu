"use client"

import { useEffect, useState } from "react"
import {
  fetchOverrides,
  createOverride,
  deleteOverride,
  type OverrideResponse,
  type OverrideCreate,
} from "@/lib/admin-api"

const HALL_IDS = ["hoch", "collins", "malott", "mcconnell", "frank", "frary", "oldenborg"]
const MEALS = ["Breakfast", "Lunch", "Dinner"]

export default function OverridesPage() {
  const [overrides, setOverrides] = useState<OverrideResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createValues, setCreateValues] = useState<OverrideCreate>({
    hall_id: HALL_IDS[0],
    date: "",
    meal: MEALS[0],
    start_time: "",
    end_time: "",
    reason: "",
  })
  const [error, setError] = useState<string | null>(null)

  const loadOverrides = () => {
    setError(null)
    fetchOverrides()
      .then(setOverrides)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadOverrides()
  }, [])

  const handleCreate = async () => {
    try {
      setError(null)
      const payload: OverrideCreate = {
        hall_id: createValues.hall_id,
        date: createValues.date,
        meal: createValues.meal || null,
        start_time: createValues.start_time || null,
        end_time: createValues.end_time || null,
        reason: createValues.reason || null,
      }
      await createOverride(payload)
      setShowCreateForm(false)
      setCreateValues({
        hall_id: HALL_IDS[0],
        date: "",
        meal: MEALS[0],
        start_time: "",
        end_time: "",
        reason: "",
      })
      loadOverrides()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create override")
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this override?")) return
    try {
      setError(null)
      await deleteOverride(id)
      loadOverrides()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete override")
    }
  }

  if (loading) {
    return <p className="text-gray-500">Loading overrides...</p>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Date Overrides</h1>
        <button
          onClick={() => setShowCreateForm((v) => !v)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showCreateForm ? "Cancel" : "Add Override"}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded text-sm">
          {error}
        </div>
      )}

      {showCreateForm && (
        <div className="mb-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
          <h2 className="text-sm font-semibold mb-3">New Override</h2>
          <p className="text-xs text-gray-500 mb-3">
            Leave start and end times empty to mark a meal as closed.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <label className="block">
              <span className="text-xs text-gray-500">Hall</span>
              <select
                value={createValues.hall_id}
                onChange={(e) => setCreateValues((v) => ({ ...v, hall_id: e.target.value }))}
                className="block w-full mt-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900"
              >
                {HALL_IDS.map((h) => (
                  <option key={h} value={h}>
                    {h}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">Date</span>
              <input
                type="date"
                value={createValues.date}
                onChange={(e) => setCreateValues((v) => ({ ...v, date: e.target.value }))}
                className="block w-full mt-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900"
              />
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">Meal</span>
              <select
                value={createValues.meal ?? ""}
                onChange={(e) => setCreateValues((v) => ({ ...v, meal: e.target.value }))}
                className="block w-full mt-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900"
              >
                {MEALS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">Start Time</span>
              <input
                type="time"
                value={createValues.start_time ?? ""}
                onChange={(e) => setCreateValues((v) => ({ ...v, start_time: e.target.value }))}
                className="block w-full mt-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900"
              />
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">End Time</span>
              <input
                type="time"
                value={createValues.end_time ?? ""}
                onChange={(e) => setCreateValues((v) => ({ ...v, end_time: e.target.value }))}
                className="block w-full mt-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900"
              />
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">Reason</span>
              <input
                type="text"
                value={createValues.reason ?? ""}
                onChange={(e) => setCreateValues((v) => ({ ...v, reason: e.target.value }))}
                placeholder="e.g. Holiday closure"
                className="block w-full mt-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900"
              />
            </label>
          </div>
          <button
            onClick={handleCreate}
            className="mt-3 px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700"
          >
            Create Override
          </button>
        </div>
      )}

      {overrides.length === 0 ? (
        <p className="text-gray-500 text-sm">No overrides yet. Click &quot;Add Override&quot; to create one.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 text-left">
                <th className="px-3 py-2 font-medium">Hall</th>
                <th className="px-3 py-2 font-medium">Date</th>
                <th className="px-3 py-2 font-medium">Meal</th>
                <th className="px-3 py-2 font-medium">Start</th>
                <th className="px-3 py-2 font-medium">End</th>
                <th className="px-3 py-2 font-medium">Reason</th>
                <th className="px-3 py-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {overrides.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900"
                >
                  <td className="px-3 py-2">{row.hall_id}</td>
                  <td className="px-3 py-2">{row.date}</td>
                  <td className="px-3 py-2">{row.meal ?? "-"}</td>
                  <td className="px-3 py-2">
                    {row.start_time ?? <span className="text-red-500 font-medium">Closed</span>}
                  </td>
                  <td className="px-3 py-2">{row.end_time ?? "-"}</td>
                  <td className="px-3 py-2 text-gray-600 dark:text-gray-400">{row.reason ?? "-"}</td>
                  <td className="px-3 py-2">
                    <button
                      onClick={() => handleDelete(row.id)}
                      className="text-red-600 hover:underline text-sm"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
