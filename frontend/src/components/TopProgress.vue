<script setup>
import { loadingStore } from '../composables/useLoading.js';
</script>

<template>
  <div class="top-progress" :class="{ on: loadingStore.visible }">
    <div
      class="top-progress-bar"
      role="progressbar"
      aria-label="数据加载进度"
      :aria-busy="loadingStore.visible"
    ></div>
    <Transition name="tip">
      <p v-if="loadingStore.slow" class="top-progress-tip" role="status">
        服务响应较慢，正在努力加载…
      </p>
    </Transition>
  </div>
</template>
