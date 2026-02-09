'use client'

import { useQuery } from '@tanstack/react-query'
import { fetchHalls, fetchMenu, fetchOpenNow } from './api'
import type { HallResponse, MenuResponse, OpenHallResponse } from './types'

export function useHalls() {
  return useQuery<HallResponse[]>({
    queryKey: ['halls'],
    queryFn: fetchHalls,
    staleTime: 5 * 60 * 1000, // halls metadata changes rarely
  })
}

export function useMenu(hallId: string, date: string, meal: string) {
  return useQuery<MenuResponse>({
    queryKey: ['menu', hallId, date, meal],
    queryFn: () => fetchMenu(hallId, date, meal),
    enabled: !!hallId && !!date && !!meal,
  })
}

export function useOpenNow() {
  return useQuery<OpenHallResponse[]>({
    queryKey: ['open-now'],
    queryFn: fetchOpenNow,
    refetchInterval: 60 * 1000, // poll every 60s for live status
  })
}
