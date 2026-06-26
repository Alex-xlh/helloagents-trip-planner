<template>
  <div class="plane-switch-wrapper">
    <!-- 提示文本 -->
    <div class="slide-text" :class="{ 'fade-out': sliding || loading || completed }">
      滑动起飞，开启定制之旅 >>
    </div>

    <!-- 加载中或完成时的状态文本 -->
    <div class="status-text" :class="{ 'fade-in': loading || completed }">
      <span v-if="loading">
        <svg class="loading-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="2" x2="12" y2="6"></line>
          <line x1="12" y1="18" x2="12" y2="22"></line>
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
          <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
          <line x1="2" y1="12" x2="6" y2="12"></line>
          <line x1="18" y1="12" x2="22" y2="12"></line>
          <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
          <line x1="16.24" y1="4.93" x2="19.07" y2="7.76"></line>
        </svg>
        规划引擎运转中...
      </span>
      <span v-else-if="completed">
        <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        起飞准备就绪
      </span>
    </div>

    <!-- Plane Switch Interactive Container -->
    <div class="plane-switch-container" 
         ref="containerRef"
         :style="containerStyles"
         :class="{ 'is-completed': completed, 'animate-return': returning, 'sliding': sliding }">
      
      <span class="street-middle"></span>
      <span class="cloud"></span>
      <span class="cloud two"></span>
      
      <div class="plane-thumb"
           :style="thumbStyles"
           @mousedown="startSlide"
           @touchstart.passive="startSlide">
        <svg viewBox="0 0 13 13">
          <path d="M1.55989957,5.41666667 L5.51582215,5.41666667 L4.47015462,0.108333333 L4.47015462,0.108333333 C4.47015462,0.0634601974 4.49708054,0.0249592654 4.5354546,0.00851337035 L4.57707145,0 L5.36229752,0 C5.43359776,0 5.50087375,0.028779451 5.55026392,0.0782711996 L5.59317877,0.134368264 L7.13659662,2.81558333 L8.29565964,2.81666667 C8.53185377,2.81666667 8.72332694,3.01067661 8.72332694,3.25 C8.72332694,3.48932339 8.53185377,3.68333333 8.29565964,3.68333333 L7.63589819,3.68225 L8.63450135,5.41666667 L11.9308317,5.41666667 C12.5213171,5.41666667 13,5.90169152 13,6.5 C13,7.09830848 12.5213171,7.58333333 11.9308317,7.58333333 L8.63450135,7.58333333 L7.63589819,9.31666667 L8.29565964,9.31666667 C8.53185377,9.31666667 8.72332694,9.51067661 8.72332694,9.75 C8.72332694,9.98932339 8.53185377,10.1833333 8.29565964,10.1833333 L7.13659662,10.1833333 L5.59317877,12.8656317 C5.55725264,12.9280353 5.49882018,12.9724157 5.43174295,12.9907056 L5.36229752,13 L4.57707145,13 L4.55610333,12.9978962 C4.51267695,12.9890959 4.48069792,12.9547924 4.47230803,12.9134397 L4.47223088,12.8704208 L5.51582215,7.58333333 L1.55989957,7.58333333 L0.891288881,8.55114605 C0.853775374,8.60544678 0.798421006,8.64327676 0.73629202,8.65879796 L0.672314689,8.66666667 L0.106844414,8.66666667 L0.0715243949,8.66058466 L0.0715243949,8.66058466 C0.0297243066,8.6457608 0.00275502199,8.60729104 0,8.5651586 L0.00593007386,8.52254537 L0.580855011,6.85813984 C0.64492547,6.67265611 0.6577034,6.47392717 0.619193545,6.28316421 L0.580694768,6.14191703 L0.00601851064,4.48064746 C0.00203480725,4.4691314 0,4.45701613 0,4.44481314 C0,4.39994001 0.0269259152,4.36143908 0.0652999725,4.34499318 L0.106916826,4.33647981 L0.672546853,4.33647981 C0.737865848,4.33647981 0.80011301,4.36066329 0.848265401,4.40322477 L0.89131128,4.45169723 L1.55989957,5.41666667 Z" fill="currentColor"></path>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, watch } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit'])

const containerRef = ref<HTMLElement | null>(null)
const thumbOffset = ref(0)
const sliding = ref(false)
const returning = ref(false)
const completed = ref(false)
const maxOffset = ref(0)

watch(() => props.loading, (newVal) => {
  if (!newVal) {
    completed.value = false
    thumbOffset.value = 0
  }
})

let startX = 0
const THUMB_WIDTH = 56 // 内边距4px所以高度56px

// 动态绑定背景等全局 CSS 变量
const containerStyles = computed(() => {
  if (maxOffset.value === 0 && !completed.value && !props.loading) return {}
  const p = completed.value || props.loading ? 1 : thumbOffset.value / maxOffset.value
  return {
    '--p': `${p * 100}%`,
    '--s': `${-p * 100}%`,
    '--co': p > 0.5 ? 0.8 : 0,
    '--co-2': p > 0.5 ? 0.6 : 0,
    '--c': p > 0.5 ? 'var(--sky-2)' : 'var(--street)'
  }
})

// 使用内联样式直接绑定 transform，确保移动端和桌面端响应无延迟
const thumbStyles = computed(() => {
  return {
    transform: `translateX(${thumbOffset.value}px) ${sliding.value ? 'scale(0.95)' : 'scale(1)'}`
  }
})

const startSlide = (e: MouseEvent | TouchEvent) => {
  if (props.loading || completed.value || returning.value) return
  
  sliding.value = true
  returning.value = false
  
  startX = e instanceof MouseEvent ? e.clientX : e.touches[0].clientX
  
  if (containerRef.value) {
    maxOffset.value = containerRef.value.offsetWidth - THUMB_WIDTH - 8
  }
  
  window.addEventListener('mousemove', onSlide)
  window.addEventListener('touchmove', onSlide, { passive: false })
  window.addEventListener('mouseup', endSlide)
  window.addEventListener('touchend', endSlide)
}

const onSlide = (e: MouseEvent | TouchEvent) => {
  if (!sliding.value) return
  
  if (e.cancelable && e.type === 'touchmove') {
    e.preventDefault()
  }
  
  const clientX = e instanceof MouseEvent ? e.clientX : e.touches[0].clientX
  let delta = clientX - startX
  
  if (delta < 0) delta = 0
  if (delta > maxOffset.value) delta = maxOffset.value
  
  thumbOffset.value = delta
}

const endSlide = () => {
  if (!sliding.value) return
  sliding.value = false
  
  window.removeEventListener('mousemove', onSlide)
  window.removeEventListener('touchmove', onSlide)
  window.removeEventListener('mouseup', endSlide)
  window.removeEventListener('touchend', endSlide)
  
  if (thumbOffset.value > maxOffset.value * 0.9) {
    thumbOffset.value = maxOffset.value
    completed.value = true
    emit('submit')
  } else {
    reset()
  }
}

const reset = () => {
  returning.value = true
  thumbOffset.value = 0
  completed.value = false
  
  setTimeout(() => {
    returning.value = false
  }, 600)
}

defineExpose({
  reset
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onSlide)
  window.removeEventListener('touchmove', onSlide)
  window.removeEventListener('mouseup', endSlide)
  window.removeEventListener('touchend', endSlide)
})
</script>

<style scoped>
.plane-switch-wrapper {
  --dot: #fff;
  --street: #6B6D76;
  --street-line: #A8AAB4;
  --street-line-mid: #C0C2C8;
  --sky-1: #60A7FA;
  --sky-2: #2F8EFC;
  --light-1: rgba(255, 233, 0, 1);
  --light-2: rgba(255, 233, 0, .3);
  width: 100%;
  margin-bottom: 24px;
  position: relative;
  user-select: none;
}

.plane-switch-container {
  -webkit-mask-image: -webkit-radial-gradient(white, black);
  mask-image: radial-gradient(white, black);
  position: relative;
  overflow: hidden;
  width: 100%;
  height: 64px;
  padding: 4px;
  border-radius: 32px;
  background: linear-gradient(90deg, var(--street) 0%, var(--street) 25%, var(--sky-1) 75%, var(--sky-2) 100%) left var(--p, 0%) top 0;
  background-size: 400% auto;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  -webkit-tap-highlight-color: transparent;
}

.plane-switch-container.animate-return {
  transition: background-position 0.6s cubic-bezier(0.2, 0.8, 0.35, 1.2);
}

.plane-switch-container::before, .plane-switch-container::after {
  content: "";
  display: block;
  position: absolute;
  transform: translateX(var(--s, 0));
}

.plane-switch-container.animate-return::before,
.plane-switch-container.animate-return::after,
.plane-switch-container.animate-return .street-middle {
  transition: transform 0.6s cubic-bezier(0.2, 0.8, 0.35, 1.2);
}

.plane-switch-container::before {
  width: 100%;
  left: 0;
  top: 10px;
  height: 2px;
  background: var(--street-line);
  box-shadow: 0 42px 0 0 var(--street-line);
}

.plane-switch-container::after {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  left: 60%;
  top: 4px;
  animation: lights2 2s linear infinite;
  box-shadow: inset 0 0 0 2px var(--light-1), 0 52px 0 var(--light-1), 20px 0 0 var(--light-2), 20px 52px 0 var(--light-2), 40px 0 0 var(--light-2), 40px 52px 0 var(--light-2);
}

.street-middle {
  display: block;
  position: absolute;
  top: 31px;
  left: 0;
  width: 100%;
  height: 2px;
  transform: translateX(var(--s, 0));
  background-image: repeating-linear-gradient(90deg, var(--street-line-mid) 0, var(--street-line-mid) 16px, transparent 16px, transparent 32px);
}

.cloud {
  display: block;
  width: 24px;
  height: 8px;
  border-radius: 4px;
  background: #fff;
  position: absolute;
  top: var(--ct, 16px);
  left: 100%;
  opacity: var(--co, 0);
  transition: opacity 0.3s;
  animation: clouds2 2s linear infinite var(--cd, 0s);
}

.cloud:before, .cloud:after {
  content: "";
  position: absolute;
  transform: translateX(var(--cx, 0));
  border-radius: 50%;
  width: var(--cs, 10px);
  height: var(--cs, 10px);
  background: #fff;
  bottom: 2px;
  left: 2px;
}

.cloud:after {
  --cs: 12px;
  --cx: 8px;
}

.cloud.two {
  --ct: 40px;
  --cd: 1s;
  opacity: var(--co-2, 0);
}

.plane-thumb {
  position: relative;
  z-index: 10;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--dot);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  cursor: grab;
  /* 防止触发浏览器原生的图片/SVG拖拽行为 */
  user-select: none;
  -webkit-user-drag: none;
  touch-action: none;
}

.plane-thumb:active, .plane-switch-container.sliding .plane-thumb {
  cursor: grabbing;
}

.plane-switch-container.animate-return .plane-thumb {
  transition: transform 0.6s cubic-bezier(0.2, 0.8, 0.35, 1.2);
}

.plane-thumb svg {
  width: 26px;
  height: 26px;
  display: block;
  color: var(--c, var(--street));
  pointer-events: none; /* 让鼠标事件穿透 SVG 直达 .plane-thumb */
}

.plane-switch-container.animate-return .plane-thumb svg {
  transition: color 0.6s;
}

/* 文本 Overlay */
.slide-text, .status-text {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  color: white;
  z-index: 20;
  pointer-events: none;
  text-shadow: 0 1px 3px rgba(0,0,0,0.6);
  transition: opacity 0.3s;
  letter-spacing: 1px;
}
.slide-text.fade-out { opacity: 0; }
.status-text { opacity: 0; }
.status-text.fade-in { opacity: 1; }

.loading-icon, .check-icon {
  width: 20px;
  height: 20px;
  margin-right: 8px;
  vertical-align: middle;
}
.loading-icon {
  animation: spin 2s linear infinite;
}

@keyframes lights2 {
  20%, 30% { box-shadow: inset 0 0 0 2px var(--light-2), 0 52px 0 var(--light-2), 20px 0 0 var(--light-1), 20px 52px 0 var(--light-1), 40px 0 0 var(--light-2), 40px 52px 0 var(--light-2); }
  55%, 65% { box-shadow: inset 0 0 0 2px var(--light-2), 0 52px 0 var(--light-2), 20px 0 0 var(--light-2), 20px 52px 0 var(--light-2), 40px 0 0 var(--light-1), 40px 52px 0 var(--light-1); }
  90%, 100% { box-shadow: inset 0 0 0 2px var(--light-1), 0 52px 0 var(--light-1), 20px 0 0 var(--light-2), 20px 52px 0 var(--light-2), 40px 0 0 var(--light-2), 40px 52px 0 var(--light-2); }
}

@keyframes clouds2 {
  97% { transform: translateX(-1500px); visibility: visible; }
  98%, 100% { visibility: hidden; }
  99% { transform: translateX(-1500px); }
  100% { transform: translateX(0); }
}
</style>
