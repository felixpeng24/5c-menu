"use client"

import { useState } from "react"
import { requestMagicLink } from "@/lib/admin-api"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await requestMagicLink(email)
      setSubmitted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send login link")
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="max-w-md mx-auto mt-20 text-center">
        <h1 className="text-2xl font-bold mb-4">Check your email</h1>
        <p className="text-gray-600 dark:text-gray-400">
          If this email is registered, a login link has been sent. Check your
          inbox and click the link to sign in.
        </p>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto mt-20">
      <h1 className="text-2xl font-bold mb-6 text-center">Admin Login</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-1">
            Email address
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@example.com"
            className="border border-gray-300 dark:border-gray-700 rounded px-3 py-2 w-full bg-white dark:bg-gray-900"
          />
        </div>
        {error && (
          <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded px-4 py-2 w-full"
        >
          {loading ? "Sending..." : "Send login link"}
        </button>
      </form>
    </div>
  )
}
