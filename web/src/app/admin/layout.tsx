import Link from "next/link"

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <nav className="border-b border-gray-200 dark:border-gray-800 px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href="/admin" className="text-lg font-semibold">
            5C Menu Admin
          </Link>
          <div className="flex gap-4 text-sm">
            <Link href="/admin/hours" className="hover:underline">Hours</Link>
            <Link href="/admin/overrides" className="hover:underline">Overrides</Link>
            <Link href="/admin/health" className="hover:underline">Health</Link>
          </div>
        </div>
      </nav>
      <main className="max-w-5xl mx-auto p-4">
        {children}
      </main>
    </div>
  )
}
