const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function adminFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}/api/v2/admin${path}`, {
    credentials: "include",
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Admin API error: ${res.status}`)
  }
  return res.json()
}

// --- Auth ---

export interface MessageResponse {
  message: string
}

export function requestMagicLink(email: string): Promise<MessageResponse> {
  return adminFetch<MessageResponse>("/auth/request-link", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  })
}

export function verifyMagicLink(token: string): Promise<MessageResponse> {
  return adminFetch<MessageResponse>("/auth/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  })
}

export function logout(): Promise<MessageResponse> {
  return adminFetch<MessageResponse>("/auth/logout", {
    method: "POST",
  })
}

// --- Hours ---

export interface HoursResponse {
  id: number
  hall_id: string
  day_of_week: number
  meal: string
  start_time: string
  end_time: string
  is_active: boolean
}

export interface HoursCreate {
  hall_id: string
  day_of_week: number
  meal: string
  start_time: string
  end_time: string
}

export interface HoursUpdate {
  start_time?: string | null
  end_time?: string | null
  is_active?: boolean | null
}

export function fetchHours(): Promise<HoursResponse[]> {
  return adminFetch<HoursResponse[]>("/hours")
}

export function createHours(data: HoursCreate): Promise<HoursResponse> {
  return adminFetch<HoursResponse>("/hours", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
}

export function updateHours(id: number, data: HoursUpdate): Promise<HoursResponse> {
  return adminFetch<HoursResponse>(`/hours/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
}

export function deleteHours(id: number): Promise<MessageResponse> {
  return adminFetch<MessageResponse>(`/hours/${id}`, {
    method: "DELETE",
  })
}

// --- Overrides ---

export interface OverrideResponse {
  id: number
  hall_id: string
  date: string
  meal: string | null
  start_time: string | null
  end_time: string | null
  reason: string | null
}

export interface OverrideCreate {
  hall_id: string
  date: string
  meal?: string | null
  start_time?: string | null
  end_time?: string | null
  reason?: string | null
}

export interface OverrideUpdate {
  start_time?: string | null
  end_time?: string | null
  reason?: string | null
}

export function fetchOverrides(): Promise<OverrideResponse[]> {
  return adminFetch<OverrideResponse[]>("/overrides")
}

export function createOverride(data: OverrideCreate): Promise<OverrideResponse> {
  return adminFetch<OverrideResponse>("/overrides", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
}

export function updateOverride(id: number, data: OverrideUpdate): Promise<OverrideResponse> {
  return adminFetch<OverrideResponse>(`/overrides/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
}

export function deleteOverride(id: number): Promise<MessageResponse> {
  return adminFetch<MessageResponse>(`/overrides/${id}`, {
    method: "DELETE",
  })
}

// --- Health ---

export interface ParserHealthResponse {
  hall_id: string
  last_success: string | null
  total_runs_24h: number
  error_count_24h: number
  error_rate: number
}

export function fetchHealth(): Promise<ParserHealthResponse[]> {
  return adminFetch<ParserHealthResponse[]>("/health")
}
