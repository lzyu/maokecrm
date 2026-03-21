import createClient from 'openapi-fetch'
import type { paths } from './generated'
import { useAuthStore } from '../stores/authStore'

// Create the API client
const client = createClient<paths>({
  baseUrl: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
client.use({
  async onRequest({ request }) {
    const accessToken = useAuthStore.getState().accessToken
    if (accessToken) {
      request.headers.set('Authorization', `Bearer ${accessToken}`)
    }
    return request
  },
  async onResponse({ response }) {
    // Handle 401 errors - redirect to login
    if (response.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return response
  },
})

export default client
