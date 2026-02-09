export interface HallResponse {
  id: string
  name: string
  college: string
  vendor_type: string
  color: string | null
}

export interface MenuItemResponse {
  name: string
  tags: string[]
}

export interface StationResponse {
  name: string
  items: MenuItemResponse[]
}

export interface MenuResponse {
  hall_id: string
  date: string
  meal: string
  stations: StationResponse[]
  is_stale: boolean
  fetched_at: string | null
}

export interface OpenHallResponse {
  id: string
  name: string
  college: string
  color: string | null
  current_meal: string
}
