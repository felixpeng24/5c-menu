import type { HallResponse, MenuResponse, OpenHallResponse } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const fetchHalls = () => apiFetch<HallResponse[]>('/api/v2/halls/')
export const fetchMenu = (hallId: string, date: string, meal: string) =>
  apiFetch<MenuResponse>(`/api/v2/menus/?hall_id=${hallId}&date=${date}&meal=${meal}`)
export const fetchOpenNow = () => apiFetch<OpenHallResponse[]>('/api/v2/open-now/')
