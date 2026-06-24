<template>
  <div class="history-container">
    <div class="glass-header">
      <h1 class="page-title">📜 我的旅行记录</h1>
    </div>

    <div v-if="loading" class="loading-state">
      <a-spin size="large" />
      <p>加载中...</p>
    </div>

    <div v-else-if="trips.length === 0" class="empty-state">
      <div class="empty-icon">🎒</div>
      <h2>你还没有规划过任何旅行</h2>
      <button class="primary-btn" @click="$router.push('/')">立即开启规划</button>
    </div>

    <div v-else class="trip-grid">
      <div 
        v-for="trip in trips" 
        :key="trip.id" 
        class="trip-card"
        @click="viewTrip(trip.id)"
      >
        <div class="trip-card-content">
          <h2 class="destination">{{ trip.destination }}</h2>
          <img v-if="trip.thumbnail" :src="trip.thumbnail" class="trip-thumbnail" alt="thumbnail" />
          <div class="trip-meta">
            <span>📅 {{ new Date(trip.created_at).toLocaleDateString() }}</span>
            <span>📆 {{ trip.travel_days }}天</span>
            <span v-if="trip.total_budget">💰 ¥{{ trip.total_budget }}</span>
          </div>
        </div>
        
        <a-popconfirm
          title="确定删除此行程？"
          ok-text="删除"
          cancel-text="取消"
          @confirm="deleteTrip(trip.id)"
        >
          <button class="delete-btn" @click.stop>✕</button>
        </a-popconfirm>
      </div>
    </div>

    <div class="pagination-wrapper" v-if="total > pageSize">
      <a-pagination
        v-model:current="currentPage"
        :total="total"
        :page-size="pageSize"
        @change="fetchTrips"
        show-size-changer
        @showSizeChange="onShowSizeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/services/api'
import { message } from 'ant-design-vue'

const router = useRouter()
const trips = ref<any[]>([])
const loading = ref(true)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const fetchTrips = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/api/history', {
      params: { page: currentPage.value, page_size: pageSize.value }
    })
    trips.value = response.data.items
    total.value = response.data.total
  } catch (error: any) {
    message.error('获取历史记录失败')
  } finally {
    loading.value = false
  }
}

const onShowSizeChange = (_current: number, size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchTrips()
}

const deleteTrip = async (id: number) => {
  try {
    await apiClient.delete(`/api/history/${id}`)
    message.success('已删除')
    fetchTrips()
  } catch (error) {
    message.error('删除失败')
  }
}

const viewTrip = async (id: number) => {
  try {
    const response = await apiClient.get(`/api/history/${id}`)
    const tripData = response.data.trip_data
    // 保存到 sessionStorage 供 Result 页面读取
    sessionStorage.setItem('tripPlan', JSON.stringify(tripData))
    router.push('/result')
  } catch (error) {
    message.error('加载详情失败')
  }
}

onMounted(() => {
  fetchTrips()
})
</script>

<style scoped>
.history-container {
  min-height: 100vh;
  padding: 100px 40px 40px;
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
  /* 类似首页的流体背景也可复用 */
}

.glass-header {
  margin-bottom: 40px;
  text-align: center;
}

.page-title {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #1890ff, #722ed1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 100px 0;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.primary-btn {
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: white;
  border: none;
  padding: 12px 32px;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 20px;
  transition: transform 0.3s;
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(24, 144, 255, 0.3);
}

.trip-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.trip-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 20px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 32px rgba(0,0,0,0.05);
}

.trip-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 12px 48px rgba(0,0,0,0.1);
  background: rgba(255, 255, 255, 0.9);
}

.destination {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 12px;
}

.trip-meta {
  color: #666;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.trip-thumbnail {
  width: 100%;
  height: 120px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 12px;
}

.delete-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(255, 0, 0, 0.1);
  color: red;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s;
}

.trip-card:hover .delete-btn {
  opacity: 1;
}

.pagination-wrapper {
  margin-top: 40px;
  display: flex;
  justify-content: center;
}
</style>
