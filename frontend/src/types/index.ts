export interface User {
  id: string
  email: string
  full_name: string
  phone?: string
  role: string
}

export interface Event {
  id: string
  title: string
  description?: string
  venue?: string
  city?: string
  event_date: string
  organizer_id: string
  category?: string
  image_url?: string
}

export interface Listing {
  id: string
  ticket_id: string
  event_id: string
  seller_user_id: string
  price: number
  description?: string
  status: 'ACTIVE' | 'SOLD' | 'BLOCKED'
  created_at: string
  event?: Event
  ticket?: {
    seat_info?: string
    face_value?: number
  }
}

export interface Order {
  id: string
  listing_id: string
  buyer_user_id: string
  status: 'PENDING_PAYMENT' | 'PAID' | 'CANCELLED' | 'FAILED'
  amount: number
  cancel_reason?: string
  created_at: string
  payment?: Payment
  reissue?: ReissueRequest
}

export interface Payment {
  id: string
  order_id: string
  provider: string
  status: 'CREATED' | 'CONFIRMED' | 'FAILED'
  amount: number
  checkout_url?: string
  created_at: string
}

export interface ReissueRequest {
  id: string
  ticket_id: string
  order_id: string
  status: 'PENDING' | 'SUCCESS' | 'FAILED'
  external_new_ticket_id?: string
  error_code?: string
  error_message?: string
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pages: number
}
