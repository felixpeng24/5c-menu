// Map college slug -> Tailwind @theme bg class (defined in globals.css)
export const COLLEGE_BG: Record<string, string> = {
  hmc: 'bg-hmc',
  cmc: 'bg-cmc',
  scripps: 'bg-scripps',
  pitzer: 'bg-pitzer',
  pomona: 'bg-pomona',
}

// Dietary tag -> label abbreviation (tags come as lowercase strings from backend)
export const DIETARY_ICONS: Record<string, string> = {
  vegan: 'V',
  vegetarian: 'VG',
  'gluten-free': 'GF',
  'contains nuts': 'N',
  halal: 'HL',
  'made without gluten': 'GF',
}

// Meal periods per hall (derived from backend HALL_CONFIG + known hall schedules)
// Oldenborg only serves lunch. All others serve breakfast, lunch, dinner.
export const HALL_MEALS: Record<string, string[]> = {
  hoch: ['breakfast', 'lunch', 'dinner'],
  collins: ['breakfast', 'lunch', 'dinner'],
  malott: ['breakfast', 'lunch', 'dinner'],
  mcconnell: ['breakfast', 'lunch', 'dinner'],
  frank: ['breakfast', 'lunch', 'dinner'],
  frary: ['breakfast', 'lunch', 'dinner'],
  oldenborg: ['lunch'],
}

// Default meal to show when no meal is actively serving
export const DEFAULT_MEAL = 'lunch'
