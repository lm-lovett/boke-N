<script setup>
defineProps({
  variant: {
    type: String,
    default: 'text' // text | card | row | table
  },
  rows: { type: Number, default: 3 },
  height: { type: String, default: '' }
});
</script>

<template>
  <div class="skeleton" :class="`sk-${variant}`" role="status" aria-label="内容加载中">
    <template v-if="variant === 'card'">
      <span class="sk-title"></span>
      <span class="sk-line"></span>
      <span class="sk-line short"></span>
      <span class="sk-block"></span>
    </template>

    <template v-else-if="variant === 'row'">
      <span v-for="i in rows" :key="i" class="sk-row"></span>
    </template>

    <template v-else-if="variant === 'table'">
      <span class="sk-head"></span>
      <span v-for="i in rows" :key="i" class="sk-tr"></span>
    </template>

    <template v-else>
      <span class="sk-title" :style="height ? { height } : null"></span>
      <span v-for="i in rows" :key="i" class="sk-line" :class="{ short: i === rows }"></span>
    </template>
  </div>
</template>
