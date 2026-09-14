<script setup>
defineProps({
  show: { type: Boolean, default: false },
  text: { type: String, default: '加载中…' }
});
</script>

<template>
  <Transition name="fade">
    <div v-if="show" class="overlay">
      <span class="spinner" aria-hidden="true"></span>
      <span class="overlay-text">{{ text }}</span>
    </div>
  </Transition>
</template>
