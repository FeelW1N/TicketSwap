import client from './client'

export const walletApi = {
  getBalance: () => client.get<{ balance: number }>('/wallet/balance'),
  topup: (amount: number) => client.post<{ status: string; topped_up: number; balance: number }>('/wallet/topup', { amount }),
  withdraw: (amount: number) => client.post<{ status: string; withdrawn: number; balance: number }>('/wallet/withdraw', { amount }),
}
