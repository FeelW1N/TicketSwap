import client from './client'
import type { Listing, PaginatedResponse } from '../types'

export const listingsApi = {
  list: (params?: {
    page?: number; per_page?: number; event_id?: string
    q?: string; city?: string; category?: string
    sort?: 'newest' | 'price_asc' | 'price_desc' | 'date_asc' | 'date_desc'
  }) => client.get<PaginatedResponse<Listing>>('/listings', { params }),

  get: (id: string) => client.get<Listing>(`/listings/${id}`),

  create: (formData: FormData) =>
    client.post<Listing>('/listings', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  cancel: (id: string) => client.delete(`/listings/${id}`),
}
