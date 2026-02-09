import type { Metadata } from 'next'
import { QueryProvider } from '@/lib/query-provider'
import './globals.css'

export const metadata: Metadata = {
  title: '5C Menu',
  description: 'Dining hall menus for the Claremont Colleges',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 antialiased">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
