import client from './client'

export const walletApi = {
  getBalance: () => client.get<{ balance: number }>('/wallet/balance'),
  withdraw: (amount: number) => client.post<{ status: string; withdrawn: number; balance: number }>('/wallet/withdraw', { amount }),
}
