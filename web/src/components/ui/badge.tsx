import type { ReactNode } from 'react'

interface BadgeProps {
  variant: 'open' | 'closed'
  children: ReactNode
}

const variantClasses: Record<BadgeProps['variant'], string> = {
  open: 'bg-green-500 text-white',
  closed: 'bg-gray-600 text-gray-300',
}

export function Badge({ variant, children }: BadgeProps) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${variantClasses[variant]}`}
    >
      {children}
    </span>
  )
}
