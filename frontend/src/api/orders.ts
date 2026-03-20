import client from './client'
import type { Order, Payment, PaginatedResponse } from '../types'

export const ordersApi = {
  create: (listingId: string) =>
    client.post<Order>('/orders', { listing_id: listingId }),

  list: (params?: { page?: number }) =>
    client.get<PaginatedResponse<Order>>('/orders', { params }),

  get: (id: string) => client.get<Order>(`/orders/${id}`),

  cancel: (id: string) => client.post<Order>(`/orders/${id}/cancel`),

  createPayment: (orderId: string) =>
    client.post<{ payment: Payment }>('/payments/create', { order_id: orderId }),

  downloadTicket: (ticketId: string) =>
    client.get<{ download_url: string; expires_in: number }>(`/tickets/${ticketId}/download`),
}
