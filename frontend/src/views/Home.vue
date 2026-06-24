<template>
  <div class="home-container">
    <!-- 背景装饰 (Liquid Glass Fluid Shapes) -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
      <div class="glass-overlay"></div>
    </div>

    <!-- 页面标题 -->
    <div class="page-header">
      <div class="icon-wrapper">
        <svg class="animated-plane" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M22 16.5L12 11L2.5 16.5C1.5 17 0.5 16 1 15L6.5 2.5C7 1.5 8 1 9 1H15C16 1 17 1.5 17.5 2.5L23 15C23.5 16 22.5 17 22 16.5Z" fill="url(#plane-gradient)" transform="rotate(45 12 12)"/>
          <defs>
            <linearGradient id="plane-gradient" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
              <stop stop-color="#0EA5E9" />
              <stop offset="1" stop-color="#38BDF8" />
            </linearGradient>
          </defs>
        </svg>
      </div>
      <h1 class="page-title">智能旅行规划</h1>
      <p class="page-subtitle">高端、优雅、个性化的 AI 旅行向导</p>
    </div>

    <a-card class="form-card" :bordered="false">
      <a-form
        :model="formData"
        layout="vertical"
        @finish="handleSubmit"
      >
        <!-- 第一步:目的地和日期 -->
        <div class="form-section">
          <div class="section-header">
            <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
            <span class="section-title">目的地与日期</span>
          </div>

          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="city" :rules="[{ required: true, message: '请输入目的地城市' }]">
                <template #label>
                  <span class="form-label">目的地城市</span>
                </template>
                <a-input
                  v-model:value="formData.city"
                  placeholder="例如: 北京"
                  size="large"
                  class="custom-input"
                >
                  <template #prefix>
                    <svg style="width:16px;height:16px;margin-right:4px;" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><path d="M9 22v-4h6v4"></path><path d="M8 6h.01"></path><path d="M16 6h.01"></path><path d="M12 6h.01"></path><path d="M12 10h.01"></path><path d="M12 14h.01"></path><path d="M16 10h.01"></path><path d="M16 14h.01"></path><path d="M8 10h.01"></path><path d="M8 14h.01"></path></svg>
                  </template>
                </a-input>
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item name="start_date" :rules="[{ required: true, message: '请选择开始日期' }]">
                <template #label>
                  <span class="form-label">开始日期</span>
                </template>
                <a-date-picker
                  v-model:value="formData.start_date"
                  style="width: 100%"
                  size="large"
                  class="custom-input"
                  placeholder="选择日期"
                />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item name="end_date" :rules="[{ required: true, message: '请选择结束日期' }]">
                <template #label>
                  <span class="form-label">结束日期</span>
                </template>
                <a-date-picker
                  v-model:value="formData.end_date"
                  style="width: 100%"
                  size="large"
                  class="custom-input"
                  placeholder="选择日期"
                />
              </a-form-item>
            </a-col>
            <a-col :span="4">
              <a-form-item>
                <template #label>
                  <span class="form-label">旅行天数</span>
                </template>
                <div class="days-display-compact">
                  <span class="days-value">{{ formData.travel_days }}</span>
                  <span class="days-unit">天</span>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 第二步:偏好设置 -->
        <div class="form-section">
          <div class="section-header">
            <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>
            <span class="section-title">偏好设置</span>
          </div>

          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="transportation">
                <template #label>
                  <span class="form-label">交通方式</span>
                </template>
                <a-select v-model:value="formData.transportation" size="large" class="custom-select">
                  <a-select-option value="公共交通">公共交通</a-select-option>
                  <a-select-option value="自驾">自驾</a-select-option>
                  <a-select-option value="步行">步行</a-select-option>
                  <a-select-option value="混合">混合方式</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="accommodation">
                <template #label>
                  <span class="form-label">住宿偏好</span>
                </template>
                <a-select v-model:value="formData.accommodation" size="large" class="custom-select">
                  <a-select-option value="经济型酒店">经济型酒店</a-select-option>
                  <a-select-option value="舒适型酒店">舒适型酒店</a-select-option>
                  <a-select-option value="豪华酒店">豪华度假酒店</a-select-option>
                  <a-select-option value="民宿">精品民宿</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="preferences">
                <template #label>
                  <span class="form-label">旅行偏好</span>
                </template>
                <div class="preference-tags">
                  <a-checkbox-group v-model:value="formData.preferences" class="custom-checkbox-group">
                    <a-checkbox value="历史文化" class="preference-tag">历史文化</a-checkbox>
                    <a-checkbox value="自然风光" class="preference-tag">自然风光</a-checkbox>
                    <a-checkbox value="美食" class="preference-tag">特色美食</a-checkbox>
                    <a-checkbox value="购物" class="preference-tag">高端购物</a-checkbox>
                    <a-checkbox value="艺术" class="preference-tag">艺术看展</a-checkbox>
                    <a-checkbox value="休闲" class="preference-tag">沉浸休闲</a-checkbox>
                  </a-checkbox-group>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 第三步:额外要求 -->
        <div class="form-section">
          <div class="section-header">
            <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            <span class="section-title">特殊要求</span>
          </div>

          <a-form-item name="free_text_input">
            <a-textarea
              v-model:value="formData.free_text_input"
              placeholder="请输入您的任何额外需求，例如：需要无障碍设施、对海鲜过敏、必须安排米其林餐厅等..."
              :rows="3"
              size="large"
              class="custom-textarea"
            />
          </a-form-item>
        </div>

        <!-- 提交按钮 -->
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            size="large"
            block
            class="submit-button"
          >
            <template v-if="!loading">
              <span>开启定制之旅</span>
              <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
            </template>
            <template v-else>
              <span>规划引擎运转中...</span>
            </template>
          </a-button>
        </a-form-item>

        <!-- 流式打字机特效区域 -->
        <a-form-item v-if="loading">
          <div class="streaming-container">
            <div class="streaming-header">
              <svg class="loading-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="4.93" x2="19.07" y2="7.76"></line></svg>
              <span class="streaming-title">AI 旅行管家正在为您思考...</span>
            </div>
            <div class="streaming-content" ref="streamingBox">
              {{ streamedText }}<span class="cursor-blink">|</span>
            </div>
          </div>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateTripPlanStream } from '@/services/api'
import apiClient from '@/services/api'
import { useAuthStore } from '@/store/auth'
import type { TripFormData } from '@/types'
import type { Dayjs } from 'dayjs'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const streamedText = ref('')
const streamingBox = ref<HTMLElement | null>(null)

const formData = reactive<Omit<TripFormData, 'start_date' | 'end_date'> & { start_date: Dayjs | null; end_date: Dayjs | null }>({
  city: '',
  start_date: null,
  end_date: null,
  travel_days: 1,
  transportation: '公共交通',
  accommodation: '经济型酒店',
  preferences: [],
  free_text_input: ''
})

// 监听日期变化,自动计算旅行天数
watch([() => formData.start_date, () => formData.end_date], ([start, end]) => {
  if (start && end) {
    const days = end.diff(start, 'day') + 1
    if (days > 0 && days <= 30) {
      formData.travel_days = days
    } else if (days > 30) {
      message.warning('旅行天数不能超过30天')
      formData.end_date = null
    } else {
      message.warning('结束日期不能早于开始日期')
      formData.end_date = null
    }
  }
})

const handleSubmit = async () => {
  if (!formData.start_date || !formData.end_date) {
    message.error('请选择日期')
    return
  }

  loading.value = true
  streamedText.value = ''

  try {
    const requestData: TripFormData = {
      city: formData.city,
      start_date: formData.start_date.format('YYYY-MM-DD'),
      end_date: formData.end_date.format('YYYY-MM-DD'),
      travel_days: formData.travel_days,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text_input: formData.free_text_input
    }

    let fullResponseText = ''
    
    await generateTripPlanStream(requestData, (chunk) => {
      fullResponseText += chunk
      
      // 我们只把不包含 ```json 的部分显示给用户（过滤掉丑陋的代码块）
      const jsonStartIndex = fullResponseText.indexOf('```json')
      if (jsonStartIndex === -1) {
        streamedText.value = fullResponseText
      } else {
        streamedText.value = fullResponseText.substring(0, jsonStartIndex)
      }
      
      // 自动滚动到底部
      if (streamingBox.value) {
        streamingBox.value.scrollTop = streamingBox.value.scrollHeight
      }
    })

    // 流结束，解析 JSON
    const jsonMatch = fullResponseText.match(/```json\s*([\s\S]*?)\s*```/)
    let tripPlanData = null
    
    if (jsonMatch && jsonMatch[1]) {
      tripPlanData = JSON.parse(jsonMatch[1])
    } else {
      // 兜底处理：如果没有找到代码块，可能大模型直接输出了 JSON，或者出错
      try {
        tripPlanData = JSON.parse(fullResponseText)
      } catch (e) {
        console.error('JSON提取失败, 原始响应:', fullResponseText)
        throw new Error('大模型返回的数据格式不正确，解析失败')
      }
    }

    sessionStorage.setItem('tripPlan', JSON.stringify(tripPlanData))
    message.success('旅行计划生成成功!')
    
    // 如果用户已登录，自动保存到历史记录
    if (authStore.isLoggedIn && tripPlanData) {
      try {
        await apiClient.post('/api/history', {
          destination: requestData.city,
          trip_data: tripPlanData
        })
        message.success('已自动存档到历史记录')
      } catch (e) {
        console.error('自动保存行程失败', e)
        message.warning('行程已生成，但自动存档失败。您可在"历史行程"页面手动保存')
      }
    }
    
    setTimeout(() => {
      router.push('/result')
    }, 500)

  } catch (error: any) {
    message.error(error.message || '生成旅行计划失败,请稍后重试')
    console.error(error)
  } finally {
    setTimeout(() => {
      loading.value = false
      streamedText.value = ''
    }, 1000)
  }
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #F0F9FF; /* Liquid Glass base bg */
  font-family: 'Jost', sans-serif;
  padding: 60px 20px;
  position: relative;
  overflow: hidden;
}

/* 动态流体背景特效 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  animation: liquidFloat 20s infinite alternate ease-in-out;
}

.circle-1 {
  width: 600px;
  height: 600px;
  top: -200px;
  left: -100px;
  background: rgba(14, 165, 233, 0.15); /* #0EA5E9 primary */
  animation-delay: 0s;
}

.circle-2 {
  width: 500px;
  height: 500px;
  top: 30%;
  right: -150px;
  background: rgba(56, 189, 248, 0.12); /* #38BDF8 secondary */
  animation-delay: -5s;
}

.circle-3 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  left: 20%;
  background: rgba(249, 115, 22, 0.08); /* #F97316 orange accent */
  animation-delay: -10s;
}

@keyframes liquidFloat {
  0% { transform: translate(0, 0) scale(1) rotate(0deg); }
  33% { transform: translate(30px, -50px) scale(1.1) rotate(10deg); }
  66% { transform: translate(-20px, 20px) scale(0.9) rotate(-5deg); }
  100% { transform: translate(0, 0) scale(1) rotate(0deg); }
}

/* 页面标题 */
.page-header {
  text-align: center;
  margin-bottom: 50px;
  animation: fadeInDown 1s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  z-index: 1;
}

.icon-wrapper {
  margin-bottom: 24px;
}

.animated-plane {
  width: 80px;
  height: 80px;
  display: inline-block;
  animation: flyAround 10s infinite cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 12px 20px rgba(14, 165, 233, 0.3));
}

@keyframes flyAround {
  0% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(15px, -10px) rotate(4deg); }
  50% { transform: translate(0, -20px) rotate(0deg); }
  75% { transform: translate(-15px, -10px) rotate(-4deg); }
  100% { transform: translate(0, 0) rotate(0deg); }
}

.page-title {
  font-family: 'Bodoni Moda', serif;
  font-size: 56px;
  font-weight: 600;
  color: #0C4A6E; /* Deep navy blue */
  margin-bottom: 16px;
  letter-spacing: -0.5px;
}

.page-subtitle {
  font-size: 18px;
  color: #475569;
  margin: 0;
  font-weight: 300;
  letter-spacing: 1px;
}

/* 表单卡片 (Liquid Glass) */
.form-card {
  max-width: 1100px;
  margin: 0 auto;
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(12, 74, 110, 0.1);
  animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.7) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

/* 表单分区 */
.form-section {
  margin-bottom: 32px;
  padding: 32px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.form-section:hover {
  box-shadow: 0 10px 30px rgba(14, 165, 233, 0.05);
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.6);
  border-color: rgba(255, 255, 255, 0.9);
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(14, 165, 233, 0.15);
}

.section-icon {
  width: 24px;
  height: 24px;
  margin-right: 12px;
  color: #0EA5E9;
}

.section-title {
  font-family: 'Bodoni Moda', serif;
  font-size: 20px;
  font-weight: 600;
  color: #0C4A6E;
}

/* 表单标签 */
.form-label {
  font-size: 14px;
  font-weight: 500;
  color: #334155;
}

/* 自定义输入框 */
.custom-input :deep(.ant-input),
.custom-input :deep(.ant-picker) {
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.custom-input :deep(.ant-input:hover),
.custom-input :deep(.ant-picker:hover) {
  border-color: #38BDF8;
}

.custom-input :deep(.ant-input:focus),
.custom-input :deep(.ant-picker-focused) {
  border-color: #0EA5E9;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
  background: #ffffff;
}

/* 自定义选择框 */
.custom-select :deep(.ant-select-selector) {
  border-radius: 12px !important;
  border: 1px solid #E2E8F0 !important;
  background: rgba(255, 255, 255, 0.8) !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  transition: all 0.3s ease;
}

.custom-select:hover :deep(.ant-select-selector) {
  border-color: #38BDF8 !important;
}

.custom-select :deep(.ant-select-focused .ant-select-selector) {
  border-color: #0EA5E9 !important;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15) !important;
  background: #ffffff !important;
}

/* 天数显示 */
.days-display-compact {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  background: #E0F2FE;
  border: 1px solid #BAE6FD;
  border-radius: 12px;
  color: #0C4A6E;
  font-weight: 600;
}

.days-display-compact .days-value {
  font-size: 20px;
  margin-right: 4px;
}

/* 偏好标签 */
.preference-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.custom-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  width: 100%;
}

.custom-checkbox-group :deep(.ant-checkbox-wrapper) {
  margin: 0 !important;
  padding: 8px 20px;
  border: 1px solid #E2E8F0;
  border-radius: 30px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  background: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  color: #475569;
}

.custom-checkbox-group :deep(.ant-checkbox-wrapper:hover) {
  border-color: #38BDF8;
  background: rgba(255, 255, 255, 0.9);
  color: #0C4A6E;
}

.custom-checkbox-group :deep(.ant-checkbox-wrapper-checked) {
  border-color: #0EA5E9;
  background: #0EA5E9;
  color: white;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
}

.custom-checkbox-group :deep(.ant-checkbox-inner) {
  display: none; /* Hide default checkbox icon for pill style */
}

/* 文本域 */
.custom-textarea :deep(.ant-input) {
  border-radius: 16px;
  border: 1px solid #E2E8F0;
  background: rgba(255, 255, 255, 0.8);
  padding: 16px;
  transition: all 0.3s ease;
}

.custom-textarea :deep(.ant-input:hover) {
  border-color: #38BDF8;
}

.custom-textarea :deep(.ant-input:focus) {
  border-color: #0EA5E9;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
  background: #ffffff;
}

/* CTA 提交按钮 */
.submit-button {
  height: 64px;
  border-radius: 32px;
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 1px;
  background: #F97316; /* CTA Orange */
  border: none;
  box-shadow: 0 10px 25px rgba(249, 115, 22, 0.3);
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.submit-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 35px rgba(249, 115, 22, 0.4);
  background: #EA580C;
}

.submit-button:active {
  transform: translateY(1px);
  box-shadow: 0 5px 15px rgba(249, 115, 22, 0.3);
}

.button-icon {
  width: 20px;
  height: 20px;
  transition: transform 0.3s ease;
}

.submit-button:hover .button-icon {
  transform: translateX(4px);
}

/* 加载状态 */
.loading-container {
  text-align: center;
  padding: 32px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 16px;
  border: 1px dashed #BAE6FD;
}

.loading-status {
  margin-top: 16px;
  color: #0EA5E9;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

/* 进度条定制 */
.custom-progress :deep(.ant-progress-bg) {
  border-radius: 8px;
}

/* 流式打字机特效区域 */
.streaming-container {
  background: rgba(15, 23, 42, 0.85); /* 深邃质感背景 */
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(56, 189, 248, 0.3);
  padding: 24px;
  margin-top: 24px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2), 0 0 20px rgba(14, 165, 233, 0.1) inset;
}

.streaming-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.loading-icon {
  width: 20px;
  height: 20px;
  color: #38BDF8;
  margin-right: 12px;
  animation: spin 2s linear infinite;
}

.streaming-title {
  color: #E0F2FE;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 1px;
}

.streaming-content {
  color: #F8FAFC;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 15px;
  line-height: 1.8;
  white-space: pre-wrap;
  min-height: 100px;
  max-height: 300px;
  overflow-y: auto;
  padding: 8px;
}

.streaming-content::-webkit-scrollbar {
  width: 6px;
}
.streaming-content::-webkit-scrollbar-thumb {
  background: rgba(56, 189, 248, 0.5);
  border-radius: 3px;
}

.cursor-blink {
  display: inline-block;
  width: 8px;
  color: #38BDF8;
  font-weight: bold;
  animation: blink 1s step-end infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 动画 */
@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-40px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
