import client from './client'
import type { Listing, PaginatedResponse } from '../types'

export const listingsApi = {
  list: (params?: { page?: number; per_page?: number; event_id?: string }) =>
    client.get<PaginatedResponse<Listing>>('/listings', { params }),

  get: (id: string) => client.get<Listing>(`/listings/${id}`),

  create: (formData: FormData) =>
    client.post<Listing>('/listings', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  cancel: (id: string) => client.delete(`/listings/${id}`),
}
