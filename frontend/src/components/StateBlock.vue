<script setup>
import { RefreshCw } from 'lucide-vue-next';

defineProps({
  tone: { type: String, default: 'empty' }, // empty | error
  title: { type: String, required: true },
  desc: { type: String, default: '' },
  retryable: { type: Boolean, default: false },
  retrying: { type: Boolean, default: false }
});

defineEmits(['retry']);
</script>

<template>
  <div class="state-block" :class="`tone-${tone}`" role="status">
    <h4 class="state-title">{{ title }}</h4>
    <p v-if="desc" class="state-desc">{{ desc }}</p>
    <button
      v-if="retryable"
      class="secondary sm state-retry"
      type="button"
      :disabled="retrying"
      @click="$emit('retry')"
    >
      <span class="row" style="gap: 6px">
        <span v-if="retrying" class="spinner spinner-sm" aria-hidden="true"></span>
        <RefreshCw v-else :size="14" />
        {{ retrying ? '重试中…' : '重试' }}
      </span>
    </button>
    <slot />
  </div>
</template>
