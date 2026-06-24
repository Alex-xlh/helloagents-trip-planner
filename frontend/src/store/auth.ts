import { reactive, computed } from 'vue'

const getValidItem = (key: string) => {
  const item = localStorage.getItem(key)
  if (item === 'null' || item === 'undefined' || !item) return null
  return item
}

// Create a single reactive state object
const state = reactive({
  token: getValidItem('token'),
  username: getValidItem('username')
})

interface TokenPayload {
  sub: string
  exp: number
  iat?: number
}

export function parseJwtPayload(token: string): TokenPayload | null {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
    )
    return JSON.parse(jsonPayload)
  } catch {
    return null
  }
}

export function isTokenExpired(token: string | null): boolean {
  if (!token) return true
  const payload = parseJwtPayload(token)
  if (!payload || !payload.exp) return true
  // 提前 5 分钟视为过期（容错）
  return (payload.exp * 1000) < (Date.now() + 5 * 60 * 1000)
}

export const useAuthStore = () => {
  const isLoggedIn = computed(() => !!state.token)

  const login = (newToken: string, newUsername: string) => {
    state.token = newToken
    state.username = newUsername
    localStorage.setItem('token', newToken)
    localStorage.setItem('username', newUsername)
  }

  const logout = () => {
    state.token = null
    state.username = null
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  // Wrapping in reactive to ensure everything (including computed) is deeply unwrapped in templates
  return reactive({
    // Using getters/setters to map to the global state object properties
    get token() { return state.token },
    get username() { return state.username },
    isLoggedIn,
    login,
    logout
  })
}
