import client from './client'
import type { Organizer, OrganizerEvent } from '../types'

export const organizersApi = {
  list: () => client.get<{ items: Organizer[] }>('/organizers'),
  listEvents: (organizerId: string) => client.get<{ items: OrganizerEvent[] }>(`/organizers/${organizerId}/events`),
}
