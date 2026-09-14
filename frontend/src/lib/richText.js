/**
 * 富文本相关的纯函数工具。
 * 后台编辑器输出 HTML，前台渲染前需要消毒，这里集中处理"HTML <-> 纯文本"的转换。
 */

const HTML_TAG_RE = /<[a-z][^>]*>/i;

/** 内容里是否含有 HTML 标签（用于兼容改造前存入的纯文本文章） */
export function looksLikeHtml(raw) {
  return HTML_TAG_RE.test(String(raw || ''));
}

/** 去掉标签、合并空白，得到可用于摘要/校验的纯文本 */
export function stripHtml(raw) {
  const text = String(raw || '');
  if (!looksLikeHtml(text)) {
    return text.replace(/\s+/g, ' ').trim();
  }
  return text
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|h[1-6]|li|blockquote|tr|pre)>/gi, '\n')
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function escapeHtml(text) {
  return text.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
}

/**
 * 把存储的内容规整成可渲染的 HTML：
 * - 富文本：原样返回，交给 DOMPurify 消毒
 * - 历史纯文本：转义后按空行分段，保证老文章不会糊成一坨
 */
export function normalizeRichText(raw) {
  const source = String(raw ?? '');
  if (!source.trim()) {
    return '';
  }
  if (looksLikeHtml(source)) {
    return source;
  }
  return source
    .split(/\n{2,}/)
    .map((block) => `<p>${escapeHtml(block.trim()).replace(/\n/g, '<br />')}</p>`)
    .join('');
}
