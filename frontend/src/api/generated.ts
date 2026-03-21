// Auto-generated types from Swagger
// Run: npm run generate-api

export type paths = Record<string, never>
export type webhooks = Record<string, never>
export interface components {
  schemas: {}
}

// Temporary manual types until generated
export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    id: number
    username: string
    email: string | null
    phone: string | null
    real_name: string | null
    avatar_url: string | null
    role_id: number
    role_name: string
    is_active: boolean
  }
}

export interface User {
  id: number
  username: string
  email: string | null
  phone: string | null
  real_name: string | null
  avatar_url: string | null
  role_id: number
  role_name: string
  is_active: boolean
  created_at: string
  updated_at: string
  last_login_at: string | null
}

export interface Customer {
  id: number
  name: string
  phone: string | null
  wechat: string | null
  email: string | null
  company: string | null
  position: string | null
  source: string | null
  status: string
  notes: string | null
  owner_id: number
  owner_name: string | null
  created_at: string
  updated_at: string
  last_followup_at: string | null
  tags: Array<{ id: number; name: string; color: string | null }>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface Tag {
  id: number
  name: string
  color: string | null
  description: string | null
  created_at: string
}
