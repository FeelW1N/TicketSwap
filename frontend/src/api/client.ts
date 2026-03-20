import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      // Пробуем обновить токен
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !error.config._retried) {
        try {
          const resp = await axios.post('/api/auth/refresh', null, {
            headers: { Authorization: `Bearer ${refreshToken}` },
          })
          const newToken = resp.data.access_token
          localStorage.setItem('access_token', newToken)
          error.config._retried = true
          error.config.headers.Authorization = `Bearer ${newToken}`
          return client(error.config)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default client
