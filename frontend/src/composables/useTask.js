import { ref } from 'vue';

/**
 * 把一个异步任务包装成带加载态响应式状态的运行器。
 *
 * 关键点是 seq 自增串号：用户连点两次时，先发出但后返回的响应会被丢弃，
 * 不会覆盖后一次请求的结果——这是"没有加载态"时最容易踩的数据错乱坑。
 *
 * @param {(signal: AbortSignal, ...args: any[]) => Promise<any>} runner
 * @param {{ onError?: (err: Error) => void }} options
 */
export function createTask(runner, options = {}) {
  const loading = ref(false);
  const loaded = ref(false);
  const error = ref('');
  let seq = 0;
  let controller = null;

  function isStale(token) {
    return token !== seq;
  }

  async function run(...args) {
    const token = (seq += 1);
    // 同一任务的上一轮请求直接作废，避免重复提交和结果互相打架
    if (controller) {
      controller.abort(new DOMException('superseded', 'AbortError'));
    }
    const current = new AbortController();
    controller = current;

    loading.value = true;
    error.value = '';
    try {
      const result = await runner(current.signal, ...args);
      if (isStale(token)) {
        return undefined;
      }
      loaded.value = true;
      return result;
    } catch (err) {
      if (isStale(token) || err?.kind === 'abort') {
        return undefined;
      }
      error.value = err?.message || '请求失败，请稍后重试';
      options.onError?.(err);
      return undefined;
    } finally {
      if (!isStale(token)) {
        loading.value = false;
        if (controller === current) {
          controller = null;
        }
      }
    }
  }

  function reset() {
    seq += 1;
    if (controller) {
      controller.abort(new DOMException('reset', 'AbortError'));
      controller = null;
    }
    loading.value = false;
    loaded.value = false;
    error.value = '';
  }

  return { loading, loaded, error, run, reset };
}
