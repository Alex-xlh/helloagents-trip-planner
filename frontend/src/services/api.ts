import axios from 'axios'
import type { TripFormData } from '@/types'
import { useAuthStore, isTokenExpired } from '@/store/auth'
import { message } from 'ant-design-vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ? API_BASE_URL : '',
  timeout: 120000, // 2分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      if (isTokenExpired(authStore.token)) {
        authStore.logout()
        message.warning('登录已过期，请重新登录')
        return Promise.reject(new Error('Token expired'))
      }
      config.headers['Authorization'] = `Bearer ${authStore.token}`
    }
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('收到响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.message)
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      message.error('登录状态已过期，请重新登录')
    }
    return Promise.reject(error)
  }
)



/**
 * 流式生成旅行计划
 */
export async function generateTripPlanStream(
  formData: TripFormData,
  onChunk: (text: string) => void
): Promise<void> {
  try {
    const baseUrlStr = import.meta.env.VITE_API_BASE_URL ? API_BASE_URL : ''
    const url = `${baseUrlStr}/api/trip/plan/stream`
    
    const authStore = useAuthStore()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }
    
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(formData)
    })

    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('流式响应读取失败')

    const decoder = new TextDecoder('utf-8')
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }
      const chunkText = decoder.decode(value, { stream: true })
      onChunk(chunkText)
    }
  } catch (error: any) {
    console.error('流式生成旅行计划失败:', error)
    throw error
  }
}

/**
 * 健康检查
 */
export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error: any) {
    console.error('健康检查失败:', error)
    throw new Error(error.message || '健康检查失败')
  }
}

export default apiClient

