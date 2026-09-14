import { reactive, readonly } from 'vue';

/**
 * 全局请求状态：驱动顶部进度条。
 *
 * 两条防抖规则，避免"快请求闪一下"的廉价感：
 * - SHOW_DELAY：150ms 内结束的请求完全不显示进度条；
 * - SLOW_THRESHOLD：超过 4s 判定为慢请求，给出文字安抚。
 */
const SHOW_DELAY = 150;
const SLOW_THRESHOLD = 4000;

const raw = reactive({
  pending: 0,
  visible: false,
  slow: false
});

let showTimer = null;
let slowTimer = null;

export const loadingStore = readonly(raw);

export function trackRequestStart() {
  raw.pending += 1;
  if (raw.pending !== 1) {
    return;
  }
  showTimer = setTimeout(() => {
    showTimer = null;
    raw.visible = true;
  }, SHOW_DELAY);
  slowTimer = setTimeout(() => {
    slowTimer = null;
    raw.slow = true;
  }, SLOW_THRESHOLD);
}

export function trackRequestEnd() {
  raw.pending = Math.max(0, raw.pending - 1);
  if (raw.pending !== 0) {
    return;
  }
  if (showTimer) {
    clearTimeout(showTimer);
    showTimer = null;
  }
  if (slowTimer) {
    clearTimeout(slowTimer);
    slowTimer = null;
  }
  raw.visible = false;
  raw.slow = false;
}
