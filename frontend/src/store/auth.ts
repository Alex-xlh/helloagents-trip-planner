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
