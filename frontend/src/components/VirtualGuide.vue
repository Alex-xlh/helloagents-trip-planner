<template>
  <div class="virtual-guide-container">
    <div v-if="errorMessage" class="error-box">{{ errorMessage }}</div>
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';

const canvasRef = ref<HTMLCanvasElement | null>(null);
const errorMessage = ref<string>('状态: 准备初始化');
let app: any = null;
let model: any = null;

onMounted(async () => {
  if (!canvasRef.value) return;

  try {
    errorMessage.value = '状态: 正在获取全局 PIXI 引擎...';
    // 直接从全局 window 获取挂载好的对象
    const PIXI = (window as any).PIXI;
    if (!PIXI || !PIXI.live2d) {
      throw new Error("PIXI 核心引擎未正确加载，请检查 index.html");
    }
    const Live2DModel = PIXI.live2d.Live2DModel;

    errorMessage.value = '状态: 正在初始化 PIXI Application...';
    app = new PIXI.Application({
      view: canvasRef.value,
      backgroundAlpha: 0,
      autoStart: true,
      width: 300,
      height: 400,
      resolution: window.devicePixelRatio || 1,
    });

    errorMessage.value = '状态: 正在加载 Live2D 模型文件...';
    const modelUrl = '/shizuku/shizuku.model.json';
    
    const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error("模型加载超时")), 10000));
    model = await Promise.race([Live2DModel.from(modelUrl), timeoutPromise]);
    
    errorMessage.value = '状态: 模型加载成功！正在设置舞台...';
    
    // 使用锚点 (Anchor) 将模型的重心定位在底部的中心
    model.anchor.set(0.5, 1);
    
    // 固定一个经验缩放比例（大部分 Cubism 模型适用）。如果模型依然偏大，可以微调这个值
    const scale = 0.2; 
    model.scale.set(scale);
    
    // 钉死在画布底部中心
    model.x = 150; 
    model.y = 400;

    app.stage.addChild(model);
    
    model.on('pointerdown', () => {
      model.motion('tap_body');
    });

    errorMessage.value = '状态: 一切就绪！(正常情况下您应该能看到模型了)';
    setTimeout(() => { errorMessage.value = ''; }, 3000);

  } catch (error: any) {
    console.error("加载 Live2D 模型失败:", error);
    errorMessage.value = "错误: " + (error.message || String(error));
  }
});

onBeforeUnmount(() => {
  if (model) {
    model.destroy();
  }
  if (app) {
    app.destroy(false, { children: true });
  }
});
</script>

<style scoped>
.virtual-guide-container {
  position: fixed;
  bottom: 0px;
  right: 20px;
  width: 300px;
  height: 400px;
  z-index: 9999; /* 悬浮在最顶层 */
  pointer-events: none; /* 让鼠标穿透透明区域，不影响底层地图点击 */
}

.virtual-guide-container canvas {
  pointer-events: auto; /* 仅捕捉模型自身的鼠标事件 */
  cursor: pointer;
  width: 100%;
  height: 100%;
}
.error-box {
  position: absolute;
  top: 10px;
  left: 10px;
  right: 10px;
  background: rgba(255, 0, 0, 0.8);
  color: white;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 10000;
  word-wrap: break-word;
}
</style>
