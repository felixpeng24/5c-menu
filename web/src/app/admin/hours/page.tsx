"use client"

import { useEffect, useState } from "react"
import {
  fetchHours,
  createHours,
  updateHours,
  deleteHours,
  type HoursResponse,
  type HoursCreate,
  type HoursUpdate,
} from "@/lib/admin-api"

const HALL_IDS = ["hoch", "collins", "malott", "mcconnell", "frank", "frary", "oldenborg"]
const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
const MEALS = ["Breakfast", "Lunch", "Dinner"]

export default function HoursPage() {
  const [hours, setHours] = useState<HoursResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editValues, setEditValues] = useState<HoursUpdate>({
    start_time: "",
    end_time: "",
    is_active: true,
  })
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createValues, setCreateValues] = useState<HoursCreate>({
    hall_id: HALL_IDS[0],
    day_of_week: 0,
    meal: MEALS[0],
    start_time: "07:00",
    end_time: "09:00",
  })
  const [error, setError] = useState<string | null>(null)

  const loadHours = () => {
    setError(null)
    fetchHours()
      .then(setHours)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadHours()
  }, [])

  const handleEdit = (row: HoursResponse) => {
    setEditingId(row.id)
    setEditValues({
      start_time: row.start_time,
      end_time: row.end_time,
      is_active: row.is_active,
    })
  }

  const handleSave = async () => {
    if (editingId === null) return
    try {
      setError(null)
      await updateHours(editingId, editValues)
      setEditingId(null)
      loadHours()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save")
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this hours entry?")) return
    try {
      setError(null)
      await deleteHours(id)
      loadHours()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete")
    }
  }

  const handleCreate = async () => {
    try {
      setError(null)
      await createHours(createValues)
      setShowCreateForm(false)
      setCreateValues({
        hall_id: HALL_IDS[0],
        day_of_week: 0,
        meal: MEALS[0],
        start_time: "07:00",
        end_time: "09:00",
      })
      loadHours()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create")
    }
  }

  if (loading) {
    return <p className="text-gray-500">Loading hours...</p>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Dining Hours</h1>
        <button
          onClick={() => setShowCreateForm((v) => !v)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showCreateForm ? "Cancel" : "Add Hours"}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded text-sm">
          {error}
        </div>
      )}

      {showCreateForm && (
        <div className="mb-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
          <h2 className="text-sm font-semibold mb-3">New Hours Entry</h2>
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
              <span className="text-xs text-gray-500">Day</span>
              <select
                value={createValues.day_of_week}
                onChange={(e) => setCreateValues((v) => ({ ...v, day_of_week: Number(e.target.value) }))}
                className="block w-full mt-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900"
              >
                {DAY_NAMES.map((d, i) => (
                  <option key={d} value={i}>
                    {d}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">Meal</span>
              <select
                value={createValues.meal}
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
                value={createValues.start_time}
                onChange={(e) => setCreateValues((v) => ({ ...v, start_time: e.target.value }))}
                className="block w-full mt-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900"
              />
            </label>
            <label className="block">
              <span className="text-xs text-gray-500">End Time</span>
              <input
                type="time"
                value={createValues.end_time}
                onChange={(e) => setCreateValues((v) => ({ ...v, end_time: e.target.value }))}
                className="block w-full mt-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900"
              />
            </label>
          </div>
          <button
            onClick={handleCreate}
            className="mt-3 px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700"
          >
            Create
          </button>
        </div>
      )}

      {hours.length === 0 ? (
        <p className="text-gray-500 text-sm">No hours entries yet. Click &quot;Add Hours&quot; to create one.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 text-left">
                <th className="px-3 py-2 font-medium">Hall</th>
                <th className="px-3 py-2 font-medium">Day</th>
                <th className="px-3 py-2 font-medium">Meal</th>
                <th className="px-3 py-2 font-medium">Start</th>
                <th className="px-3 py-2 font-medium">End</th>
                <th className="px-3 py-2 font-medium">Active</th>
                <th className="px-3 py-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {hours.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900"
                >
                  <td className="px-3 py-2">{row.hall_id}</td>
                  <td className="px-3 py-2">{DAY_NAMES[row.day_of_week] ?? row.day_of_week}</td>
                  <td className="px-3 py-2">{row.meal}</td>

                  {editingId === row.id ? (
                    <>
                      <td className="px-3 py-2">
                        <input
                          type="time"
                          value={editValues.start_time ?? ""}
                          onChange={(e) => setEditValues((v) => ({ ...v, start_time: e.target.value }))}
                          className="border border-gray-300 dark:border-gray-600 rounded px-1.5 py-0.5 text-sm bg-white dark:bg-gray-900 w-28"
                        />
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="time"
                          value={editValues.end_time ?? ""}
                          onChange={(e) => setEditValues((v) => ({ ...v, end_time: e.target.value }))}
                          className="border border-gray-300 dark:border-gray-600 rounded px-1.5 py-0.5 text-sm bg-white dark:bg-gray-900 w-28"
                        />
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="checkbox"
                          checked={editValues.is_active ?? true}
                          onChange={(e) => setEditValues((v) => ({ ...v, is_active: e.target.checked }))}
                        />
                      </td>
                      <td className="px-3 py-2 space-x-2">
                        <button onClick={handleSave} className="text-blue-600 hover:underline text-sm">
                          Save
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="text-gray-500 hover:underline text-sm"
                        >
                          Cancel
                        </button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-3 py-2">{row.start_time}</td>
                      <td className="px-3 py-2">{row.end_time}</td>
                      <td className="px-3 py-2">{row.is_active ? "Yes" : "No"}</td>
                      <td className="px-3 py-2 space-x-2">
                        <button
                          onClick={() => handleEdit(row)}
                          className="text-blue-600 hover:underline text-sm"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(row.id)}
                          className="text-red-600 hover:underline text-sm"
                        >
                          Delete
                        </button>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
