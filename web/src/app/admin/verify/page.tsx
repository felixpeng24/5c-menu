"use client"

import { useEffect, useState, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { verifyMagicLink } from "@/lib/admin-api"

function VerifyContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying")
  const [errorMessage, setErrorMessage] = useState("")

  useEffect(() => {
    const token = searchParams.get("token")
    if (!token) {
      setStatus("error")
      setErrorMessage("No token provided")
      return
    }
    verifyMagicLink(token)
      .then(() => {
        setStatus("success")
        router.push("/admin/hours")
      })
      .catch((err) => {
        setStatus("error")
        setErrorMessage(err instanceof Error ? err.message : "Verification failed")
      })
  }, [searchParams, router])

  if (status === "verifying") {
    return (
      <div className="text-center mt-20">
        <p className="text-lg">Verifying your login...</p>
      </div>
    )
  }

  if (status === "success") {
    return (
      <div className="text-center mt-20">
        <p className="text-lg">Redirecting...</p>
      </div>
    )
  }

  return (
    <div className="text-center mt-20">
      <h1 className="text-2xl font-bold mb-4 text-red-600 dark:text-red-400">
        Verification failed
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-4">{errorMessage}</p>
      <Link href="/admin/login" className="text-blue-600 hover:underline">
        Try again
      </Link>
    </div>
  )
}

export default function VerifyPage() {
  return (
    <Suspense fallback={<div className="text-center mt-20">Loading...</div>}>
      <VerifyContent />
    </Suspense>
  )
}
