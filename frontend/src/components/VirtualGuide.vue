<template>
  <div 
    class="virtual-guide-container" 
    :style="containerStyle" 
    @mousedown="onMouseDown"
  >
    <!-- 聊天气泡 -->
    <div class="chat-bubble" v-if="chatMessage">
      {{ chatMessage }}
    </div>
    
    <canvas ref="canvasRef"></canvas>
    
    <!-- 聊天输入框 (不再遮挡，按顺序排布) -->
    <div class="chat-input-container" v-if="isReady">
      <input 
        v-model="inputText" 
        @keyup.enter="handleSend" 
        placeholder="和向导聊聊..." 
        :disabled="isSpeaking"
        @mousedown.stop
      />
      <!-- 麦克风按钮 -->
      <button 
        class="icon-btn" 
        @click="toggleRecording" 
        :class="{ recording: isRecording }"
        @mousedown.stop
        title="语音输入"
      >
        🎙️
      </button>
      <button 
        class="primary-btn"
        @click="handleSend" 
        :disabled="isSpeaking || !inputText.trim()"
        @mousedown.stop
      >发送</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';

const canvasRef = ref<HTMLCanvasElement | null>(null);
const chatMessage = ref<string>('');
const inputText = ref<string>('');
const isReady = ref<boolean>(false);
const isSpeaking = ref<boolean>(false);
const isRecording = ref<boolean>(false);
const chatHistory = ref<{role: string, content: string}[]>([]); // 智能体的短期记忆

let app: any = null;
let model: any = null;
let audioContext: AudioContext | null = null;
let audioSource: AudioBufferSourceNode | null = null;
let recognition: any = null;

// ================= 拖拽逻辑 =================
const position = ref({ x: window.innerWidth - 340, y: window.innerHeight - 500 });
const containerStyle = computed(() => ({
  left: `${position.value.x}px`,
  top: `${position.value.y}px`
}));

let isDragging = false;
let startPos = { x: 0, y: 0 };
let startOffset = { x: 0, y: 0 };

const onMouseDown = (e: MouseEvent) => {
  isDragging = true;
  startPos = { x: e.clientX, y: e.clientY };
  startOffset = { x: position.value.x, y: position.value.y };
  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
};

const onMouseMove = (e: MouseEvent) => {
  if (!isDragging) return;
  let newX = startOffset.x + (e.clientX - startPos.x);
  let newY = startOffset.y + (e.clientY - startPos.y);
  
  // 边界限制，让它能在上半部分甚至任何地方移动，只要不完全出屏幕
  if(newX < -150) newX = -150;
  if(newY < -50) newY = -50;
  if(newX > window.innerWidth - 150) newX = window.innerWidth - 150;
  if(newY > window.innerHeight - 100) newY = window.innerHeight - 100;
  
  position.value.x = newX;
  position.value.y = newY;
};

const onMouseUp = () => {
  isDragging = false;
  document.removeEventListener('mousemove', onMouseMove);
  document.removeEventListener('mouseup', onMouseUp);
};

// ================= 语音识别逻辑 (麦克风) =================
const initSpeechRecognition = () => {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("当前浏览器不支持 Web Speech API");
    return;
  }
  recognition = new SpeechRecognition();
  recognition.lang = 'zh-CN';
  recognition.interimResults = false;
  recognition.continuous = false;

  recognition.onresult = (event: any) => {
    const transcript = event.results[0][0].transcript;
    inputText.value = transcript;
    isRecording.value = false;
    handleSend(); // 语音识别结束后自动发送
  };

  recognition.onerror = (event: any) => {
    console.error("语音识别错误:", event.error);
    isRecording.value = false;
  };

  recognition.onend = () => {
    isRecording.value = false;
  };
};

const toggleRecording = () => {
  if (!recognition) {
    alert("您的浏览器不支持语音输入功能。");
    return;
  }
  if (isRecording.value) {
    recognition.stop();
    isRecording.value = false; // 强制立刻更新状态，防止UI卡死
  } else {
    inputText.value = '';
    try {
      recognition.start();
      isRecording.value = true;
    } catch(e) {
      console.warn("录音已在运行中", e);
    }
  }
};

// ================= 自定义 Web Audio 播放与口型同步 =================
const playAudioWithLipSync = async (audioUrl: string) => {
  if (!audioContext) {
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  if (audioContext.state === 'suspended') {
    await audioContext.resume();
  }

  const response = await fetch(audioUrl);
  const arrayBuffer = await response.arrayBuffer();
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

  return new Promise<void>((resolve) => {
    audioSource = audioContext!.createBufferSource();
    audioSource.buffer = audioBuffer;

    const analyser = audioContext!.createAnalyser();
    analyser.fftSize = 256;
    // 关键优化：大幅削弱平滑滤镜，让音量突变立刻反映，消除首字吞音
    analyser.smoothingTimeConstant = 0.1; 
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    audioSource.connect(analyser);
    analyser.connect(audioContext!.destination);

    audioSource.onended = () => {
      resolve();
    };

    // 先启动动画循环，让它准备好
    const updateLipSync = () => {
      if (!isSpeaking.value || !model) return;
      analyser.getByteFrequencyData(dataArray);
      
      let sum = 0;
      for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i];
      }
      const average = sum / bufferLength;
      
      let mouthValue = 0;
      // 过滤极微小的底噪
      if (average > 1) { 
        let normalized = average / 255;
        // 关键优化：非线性超强增益。将小音量极速放大 5 倍
        mouthValue = normalized * 5.0; 
        
        // 关键优化：只要有声音，嘴巴至少张开 30%，告别“跟不上”的错觉
        if (mouthValue < 0.3) mouthValue = 0.3; 
        if (mouthValue > 1.0) mouthValue = 1.0;
      }
      
      // 直接设置内部物理参数
      if (model.internalModel && model.internalModel.coreModel) {
        model.internalModel.coreModel.setParamFloat('PARAM_MOUTH_OPEN_Y', mouthValue);
      }
      
      requestAnimationFrame(updateLipSync);
    };
    
    requestAnimationFrame(updateLipSync);
    
    // 动画循环就位后再开始发声
    audioSource.start(0);
  });
};

// ================= 发送消息逻辑 =================
const handleSend = async () => {
  const text = inputText.value.trim();
  if (!text || isSpeaking.value) return;
  
  try {
    isSpeaking.value = true;
    chatMessage.value = '让我想想哦... (●\'◡\'●)';
    inputText.value = ''; 
    
    // 1. 调用大模型 (LLM) 接口获取回答，携带短期记忆
    const chatResponse = await fetch('/api/guide/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        text: text,
        history: chatHistory.value // 传入上下文
      })
    });
    
    if (!chatResponse.ok) throw new Error(`LLM Error: ${chatResponse.status}`);
    const chatData = await chatResponse.json();
    const replyText = chatData.reply;
    
    // 更新短期记忆
    chatHistory.value.push({ role: 'user', content: text });
    chatHistory.value.push({ role: 'assistant', content: replyText });
    
    // 限制前端记忆长度 (保留最近 10 条)
    if (chatHistory.value.length > 10) {
      chatHistory.value = chatHistory.value.slice(-10);
    }
    
    // 2. 调用 TTS 接口将回答转成语音
    const ttsResponse = await fetch('/api/tts/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: replyText })
    });
    
    if (!ttsResponse.ok) throw new Error(`TTS Error: ${ttsResponse.status}`);
    const ttsData = await ttsResponse.json();
    const audioUrl = ttsData.url;
    
    // 关键优化：时序对齐，音频准备就绪后再让字出来，消除等待的割裂感
    chatMessage.value = replyText;
    
    // 3. 播放并触发同步口型
    await playAudioWithLipSync(audioUrl);
    
    // 气泡停留一段时间后消失
    setTimeout(() => {
      if (chatMessage.value === replyText) chatMessage.value = '';
    }, 3000);

  } catch (error: any) {
    console.error("对话链路失败:", error);
    chatMessage.value = "呜呜，大脑或者声带断线啦...";
    setTimeout(() => { chatMessage.value = ''; }, 3000);
  } finally {
    isSpeaking.value = false;
    // 强制闭嘴复位
    if (model && model.internalModel && model.internalModel.coreModel) {
        model.internalModel.coreModel.setParamFloat('PARAM_MOUTH_OPEN_Y', 0);
    }
  }
};

onMounted(async () => {
  if (!canvasRef.value) return;
  initSpeechRecognition();

  try {
    console.log('[Live2D] 正在获取全局 PIXI 引擎...');
    const PIXI = (window as any).PIXI;
    if (!PIXI || !PIXI.live2d) throw new Error("PIXI 核心引擎未挂载");
    const Live2DModel = PIXI.live2d.Live2DModel;

    console.log('[Live2D] 初始化 PIXI Application...');
    app = new PIXI.Application({
      view: canvasRef.value,
      backgroundAlpha: 0,
      autoStart: true,
      width: 300,
      height: 400,
      resolution: window.devicePixelRatio || 1,
    });

    console.log('[Live2D] 开始加载模型文件...');
    const modelUrl = '/shizuku/shizuku.model.json';
    const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error("模型加载超时")), 10000));
    model = await Promise.race([Live2DModel.from(modelUrl), timeoutPromise]);
    
    console.log('[Live2D] 模型加载成功！设置舞台...');
    model.anchor.set(0.5, 1);
    model.scale.set(0.2); 
    model.x = 150; 
    model.y = 400;

    app.stage.addChild(model);
    
    // 点击触发肢体动作
    model.on('pointerdown', () => {
      model.motion('tap_body');
    });

    console.log('[Live2D] 虚拟导游一切就绪！');
    isReady.value = true;

  } catch (error: any) {
    console.error("[Live2D] 致命错误:", error);
  }
});

onBeforeUnmount(() => {
  if (audioSource) audioSource.stop();
  if (audioContext) audioContext.close();
  if (model) model.destroy();
  if (app) app.destroy(false, { children: true });
});
</script>

<style scoped>
.virtual-guide-container {
  position: fixed;
  width: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 9999;
  cursor: grab;
  /* 捕获鼠标事件以支持拖拽，但在模型透明区域能点下去 */
  pointer-events: auto; 
}

.virtual-guide-container:active {
  cursor: grabbing;
}

.chat-bubble {
  position: relative;
  background: white;
  color: #333;
  padding: 10px 16px;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  font-size: 14px;
  white-space: nowrap;
  animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  margin-bottom: -50px; /* 大幅下沉，贴近虚拟人头部 */
  z-index: 10000;
  pointer-events: none; /* 防止干扰拖拽 */
}

.chat-bubble::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  border-width: 8px 8px 0;
  border-style: solid;
  border-color: white transparent transparent transparent;
}

.virtual-guide-container canvas {
  width: 300px;
  height: 400px;
  /* 关键：穿透画布允许拖拽 */
  pointer-events: none; 
}

.chat-input-container {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,0.95);
  padding: 8px 12px;
  border-radius: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  margin-top: -10px; /* 紧贴画布底部，不遮挡人物本身 */
  z-index: 10001;
  pointer-events: auto; /* 允许点击输入框 */
}

.chat-input-container input {
  border: none;
  background: transparent;
  outline: none;
  padding: 4px;
  font-size: 14px;
  width: 130px;
  color: #333;
}

.icon-btn {
  border: none;
  background: transparent;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: rgba(0,0,0,0.05);
}

.icon-btn.recording {
  background: #ff4757;
  color: white;
  animation: pulse 1.5s infinite;
}

.primary-btn {
  border: none;
  background: #007bff;
  color: white;
  border-radius: 16px;
  padding: 6px 14px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.primary-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

@keyframes popIn {
  from { opacity: 0; transform: translateY(10px) scale(0.9); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes pulse {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.4); }
  70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(255, 71, 87, 0); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 71, 87, 0); }
}
</style>
