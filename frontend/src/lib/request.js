import { trackRequestEnd, trackRequestStart } from '../composables/useLoading.js';

const DEFAULT_TIMEOUT = 20000;

export class ApiError extends Error {
  constructor(message, kind = 'unknown', status = 0) {
    super(message);
    this.name = 'ApiError';
    // timeout | abort | network | http | business | parse
    this.kind = kind;
    this.status = status;
  }
}

function mergeSignal(controller, externalSignal) {
  if (!externalSignal) {
    return null;
  }
  const relay = () => controller.abort(externalSignal.reason);
  if (externalSignal.aborted) {
    relay();
    return null;
  }
  externalSignal.addEventListener('abort', relay, { once: true });
  return relay;
}

/**
 * 统一请求出口。
 *
 * 相比裸 fetch 增加的保障：
 * - 超时中断（默认 20s），避免后端挂起时页面永久转圈；
 * - 错误被规范化成 ApiError，UI 层不必再猜 err.message；
 * - 自动纳入全局 pending 计数，驱动顶部进度条。
 */
export async function request(path, options = {}, token = '', config = {}) {
  const { timeout = DEFAULT_TIMEOUT, signal: externalSignal } = config;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new DOMException('timeout', 'TimeoutError')), timeout);
  const relay = mergeSignal(controller, externalSignal);

  trackRequestStart();
  let res;
  let raw;
  try {
    res = await fetch(`${import.meta.env.VITE_API_BASE ?? ''}${path}`, {
      ...options,
      headers,
      signal: controller.signal
    });
    raw = await res.text();
  } catch (err) {
    const aborted = err?.name === 'AbortError' || err?.name === 'TimeoutError';
    if (!aborted) {
      throw new ApiError('网络异常，请检查网络后重试', 'network');
    }
    if (externalSignal?.aborted) {
      throw new ApiError('请求已取消', 'abort');
    }
    throw new ApiError(`请求超时（${Math.round(timeout / 1000)} 秒），请稍后重试`, 'timeout');
  } finally {
    clearTimeout(timer);
    if (relay && externalSignal) {
      externalSignal.removeEventListener('abort', relay);
    }
    trackRequestEnd();
  }

  if (raw.trimStart().startsWith('<')) {
    throw new ApiError('接口返回异常，请稍后重试', 'parse');
  }

  let payload = null;
  try {
    payload = raw ? JSON.parse(raw) : null;
  } catch {
    throw new ApiError('响应解析失败，请稍后重试', 'parse');
  }

  if (!res.ok) {
    throw new ApiError(payload?.message || `请求失败（${res.status}）`, 'http', res.status);
  }
  if (payload && payload.success === false) {
    throw new ApiError(payload.message || '请求失败', 'business', res.status);
  }
  return payload?.data;
}
