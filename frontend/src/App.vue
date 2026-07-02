<template>
  <div id="app">
    <NavBar />
    <router-view />
    <VirtualGuide />
  </div>
</template>

<script setup lang="ts">
import NavBar from '@/components/NavBar.vue'
import VirtualGuide from '@/components/VirtualGuide.vue'
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif;
}
</style>

