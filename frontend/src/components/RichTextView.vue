<script setup>
/**
 * 前台富文本渲染。
 *
 * 渲染的是"用户在后台输入的内容"，因此安全是这个组件的第一约束：
 * - 内容经 DOMPurify 白名单消毒后才交给 v-html，script/iframe/on* 事件一律丢弃；
 * - 外链统一加 rel="noopener noreferrer"；
 * - 图片强制 loading="lazy"，长文首屏不被拖慢；
 * - 只在存在代码块时才动态加载 prismjs 做语法高亮，普通文章不付这个体积。
 */
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import DOMPurify from 'dompurify';
import { normalizeRichText } from '../lib/richText.js';

const props = defineProps({
  content: { type: String, default: '' }
});

const root = ref(null);

const ALLOWED_TAGS = [
  'p', 'br', 'hr', 'span', 'div',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'strong', 'em', 'u', 's', 'del', 'sub', 'sup', 'mark',
  'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
  'a', 'img', 'figure', 'figcaption',
  'table', 'thead', 'tbody', 'tr', 'th', 'td'
];

const ALLOWED_ATTR = ['href', 'target', 'rel', 'src', 'alt', 'title', 'class', 'colspan', 'rowspan'];

// 消毒后仍要做的事：外链加固、图片懒加载
let hookInstalled = false;
function installHook() {
  if (hookInstalled) {
    return;
  }
  hookInstalled = true;
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'A') {
      const href = node.getAttribute('href') || '';
      if (/^https?:\/\//i.test(href)) {
        node.setAttribute('target', '_blank');
        node.setAttribute('rel', 'noopener noreferrer');
      } else {
        node.removeAttribute('href');
      }
    }
    if (node.tagName === 'IMG') {
      node.setAttribute('loading', 'lazy');
      node.setAttribute('decoding', 'async');
    }
  });
}

const html = computed(() => {
  installHook();
  return DOMPurify.sanitize(normalizeRichText(props.content), {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input'],
    FORBID_ATTR: ['srcset', 'onerror', 'onload', 'onclick']
  });
});

let prismReady = false;
async function highlight() {
  if (!root.value || !root.value.querySelector('pre code')) {
    return;
  }
  try {
    if (!prismReady) {
      const { default: Prism } = await import('prismjs');
      await Promise.all([
        import('prismjs/components/prism-bash.js'),
        import('prismjs/components/prism-json.js'),
        import('prismjs/components/prism-sql.js'),
        import('prismjs/components/prism-python.js'),
        import('prismjs/components/prism-typescript.js')
      ]).catch(() => {});
      prismReady = true;
      window.Prism = window.Prism || Prism;
    }
    window.Prism.highlightAllUnder(root.value);
  } catch {
    // 高亮失败不影响正文阅读
  }
}

onMounted(highlight);
watch(html, () => nextTick(highlight));
</script>

<template>
  <div ref="root" class="rich-text" v-html="html"></div>
</template>
