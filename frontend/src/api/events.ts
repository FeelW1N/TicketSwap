import client from './client'
import type { Event, PaginatedResponse } from '../types'

export const eventsApi = {
  list: (params?: { q?: string; city?: string; page?: number }) =>
    client.get<PaginatedResponse<Event>>('/events', { params }),

  get: (id: string) => client.get<Event>(`/events/${id}`),
}
