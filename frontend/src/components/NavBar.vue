<template>
  <div class="global-navbar">
    <div class="logo" @click="goHome">
      <span class="logo-icon">🌍</span>
    </div>
    
    <div class="nav-actions">
      <template v-if="authStore.isLoggedIn">
        <a-dropdown placement="bottomRight">
          <div class="user-avatar">
            <span class="avatar-text">{{ userInitial }}</span>
          </div>
          <template #overlay>
            <a-menu class="glass-menu" @click="handleMenuClick">
              <a-menu-item key="username" disabled>
                <span style="color: #1890ff; font-weight: 500;">Hi, {{ authStore.username }}</span>
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="history">
                📜 我的历史行程
              </a-menu-item>
              <a-menu-item key="logout">
                退出登录
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </template>
      <template v-else>
        <button class="glass-btn primary" @click="showLogin = true">登录 / 注册</button>
      </template>
    </div>

    <!-- 登录注册弹窗 -->
    <a-modal 
      v-model:open="showLogin" 
      :title="isLoginMode ? '欢迎回来' : '注册账号'"
      :footer="null"
      :class="'glass-modal'"
      centered
      width="400px"
    >
      <a-form :model="formState" layout="vertical" class="auth-form" @finish="onFinish">
        <a-form-item 
          label="用户名" 
          name="username" 
          :rules="[
            { required: true, message: '请输入用户名' },
            { min: 2, message: '用户名至少2位' }
          ]"
          :extra="!isLoginMode ? '要求：至少 2 位字符' : ''"
        >
          <a-input v-model:value="formState.username" placeholder="输入用户名" size="large" />
        </a-form-item>
        
        <a-form-item 
          label="密码" 
          name="password" 
          :rules="[
            { required: true, message: '请输入密码' },
            { validator: validatePasswordStrength, trigger: 'change' }
          ]"
          :extra="!isLoginMode ? '要求：至少 6 位，且不能全为数字' : ''"
        >
          <a-input-password v-model:value="formState.password" placeholder="输入密码" size="large" />
        </a-form-item>

        <a-form-item
          v-if="!isLoginMode"
          label="确认密码"
          name="confirmPassword"
          :rules="[
            { required: true, message: '请再次输入密码' },
            { validator: validateConfirmPassword, trigger: 'change' }
          ]"
        >
          <a-input-password v-model:value="formState.confirmPassword" placeholder="再次输入密码" size="large" />
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" size="large" block :loading="loading" class="submit-btn">
            {{ isLoginMode ? '登 录' : '注 册' }}
          </a-button>
        </a-form-item>

        <div class="switch-mode">
          <a @click="isLoginMode = !isLoginMode">
            {{ isLoginMode ? '没有账号？去注册' : '已有账号？去登录' }}
          </a>
        </div>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import apiClient from '@/services/api'
import { message } from 'ant-design-vue'

const router = useRouter()
const authStore = useAuthStore()

const showLogin = ref(false)
const isLoginMode = ref(true)
const loading = ref(false)

const userInitial = computed(() => {
  return authStore.username ? authStore.username.charAt(0).toUpperCase() : ''
})

const formState = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const validatePasswordStrength = async (_rule: any, value: string) => {
  if (!value) {
    return Promise.resolve() // Handled by required rule
  }
  if (value.length < 6) {
    return Promise.reject('密码至少需要6位')
  }
  if (!isLoginMode.value && /^\d+$/.test(value)) {
    return Promise.reject('密码不能为纯数字')
  }
  return Promise.resolve()
}

const validateConfirmPassword = async (_rule: any, value: string) => {
  if (value && value !== formState.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const goHome = () => {
  router.push('/')
}

const handleMenuClick = ({ key }: { key: string }) => {
  if (key === 'history') {
    router.push('/history')
  } else if (key === 'logout') {
    authStore.logout()
    message.success('已退出登录')
    if (router.currentRoute.value.path === '/history') {
      router.push('/')
    }
  }
}

const onFinish = async () => {
  loading.value = true
  try {
    const endpoint = isLoginMode.value ? '/api/auth/login' : '/api/auth/register'
    
    const response = await apiClient.post(endpoint, {
      username: formState.username,
      password: formState.password
    })

    // 注册和登录现在都返回 {access_token, token_type}
    const { access_token } = response.data
    authStore.login(access_token, formState.username)
    
    if (!isLoginMode.value) {
      message.success('注册成功，已自动登录')
    } else {
      message.success('登录成功')
    }
    showLogin.value = false
  } catch (error: any) {
    if (error.response && error.response.data && error.response.data.detail) {
      const detail = error.response.data.detail
      if (Array.isArray(detail)) {
        // FastAPI validation error
        message.error(detail[0].msg)
      } else {
        message.error(detail)
      }
    } else {
      message.error(isLoginMode.value ? '登录失败' : '注册失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.global-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  z-index: 1000;
  background: transparent;
  pointer-events: none; /* 穿透点击，防止挡住下方元素 */
}

.global-navbar > * {
  pointer-events: auto; /* 恢复子元素的点击事件 */
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

.glass-btn {
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 8px 24px;
  border-radius: 20px;
  font-weight: 500;
  color: #1a1a1a;
  cursor: pointer;
  transition: all 0.3s ease;
}

.glass-btn:hover {
  background: rgba(255, 255, 255, 0.5);
  transform: translateY(-1px);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #722ed1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  cursor: pointer;
  border: 2px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transition: transform 0.3s;
}

.user-avatar:hover {
  transform: scale(1.05);
}

.auth-form {
  padding: 20px 0 0;
}

.submit-btn {
  border-radius: 8px;
  height: 44px;
  background: linear-gradient(135deg, #1890ff, #096dd9);
  border: none;
  font-weight: bold;
}

.switch-mode {
  text-align: center;
  margin-top: 10px;
}

:deep(.glass-modal .ant-modal-content) {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(30px) !important;
  -webkit-backdrop-filter: blur(30px) !important;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.5);
}
</style>
