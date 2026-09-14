<script setup>
/**
 * 后台富文本编辑器（wangEditor v5）。
 *
 * 设计取舍：
 * - 只在组件挂载时创建编辑器，卸载时 destroy，避免切换管理分区泄漏实例；
 * - 内容通过 v-model 以 HTML 字符串进出，与后端 articles.content 字段直接对齐；
 * - 图片优先走后端上传接口，接口不存在时自动降级为 base64 内联，
 *   保证"后端还没准备好"也不会阻塞写作（降级会向上抛 notice 提示）；
 * - 小图（≤256KB）直接内联，省一次往返。
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { createEditor, createToolbar } from '@wangeditor/editor';
import '@wangeditor/editor/dist/css/style.css';

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '开始写作…支持标题、加粗、列表、代码、表格与图片' },
  disabled: { type: Boolean, default: false },
  token: { type: String, default: '' },
  uploadUrl: { type: String, default: '/api/upload' }
});

const emit = defineEmits(['update:modelValue', 'notice']);

const toolbarEl = ref(null);
const editableEl = ref(null);
const focused = ref(false);

let editor = null;
let toolbar = null;
// 编辑器 change 回写 v-model 时，避免再被 watch 反向灌回编辑器造成光标跳动
let syncingFromProp = false;

const INLINE_LIMIT = 256 * 1024;
const MAX_SIZE = 5 * 1024 * 1024;

function readAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('读取图片失败'));
    reader.readAsDataURL(file);
  });
}

async function uploadImage(file, insertFn) {
  if (file.size > MAX_SIZE) {
    emit('notice', `图片超过 ${MAX_SIZE / 1024 / 1024}MB，请压缩后再上传`);
    return;
  }
  if (file.size <= INLINE_LIMIT) {
    insertFn(await readAsDataURL(file), file.name, '');
    return;
  }
  try {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${import.meta.env.VITE_API_BASE ?? ''}${props.uploadUrl}`, {
      method: 'POST',
      body: form,
      headers: props.token ? { Authorization: `Bearer ${props.token}` } : undefined
    });
    const data = await res.json().catch(() => null);
    const url = data?.data?.url || data?.url || data?.data?.src;
    if (!res.ok || typeof url !== 'string' || !url) {
      throw new Error('upload unavailable');
    }
    insertFn(url, file.name, '');
  } catch {
    // 后端暂无上传接口时兜底内联，写作流程不中断
    insertFn(await readAsDataURL(file), file.name, '');
    emit('notice', '图片上传接口不可用，已内联为 base64；建议后端补齐 /api/upload');
  }
}

onMounted(() => {
  editor = createEditor({
    selector: editableEl.value,
    html: props.modelValue || '<p><br></p>',
    config: {
      placeholder: props.placeholder,
      readOnly: props.disabled,
      autoFocus: false,
      scroll: false,
      MENU_CONF: {
        uploadImage: {
          allowedFileTypes: ['image/*'],
          maxFileSize: MAX_SIZE,
          customUpload: uploadImage
        }
      },
      onChange(editorInstance) {
        syncingFromProp = true;
        emit('update:modelValue', editorInstance.getHtml());
      }
    },
    mode: 'default'
  });

  editor.on('focus', () => (focused.value = true));
  editor.on('blur', () => (focused.value = false));

  toolbar = createToolbar({
    editor,
    selector: toolbarEl.value,
    config: {
      // 视频需要上传/外链能力，当前后端未提供，先收起来避免误点报错
      excludeKeys: ['uploadVideo', 'insertVideo', 'group-video', 'fullScreen']
    },
    mode: 'default'
  });
});

watch(
  () => props.modelValue,
  (next) => {
    if (!editor || editor.isDestroyed) {
      return;
    }
    if (syncingFromProp) {
      syncingFromProp = false;
      return;
    }
    if (next !== editor.getHtml()) {
      editor.setHtml(next || '<p><br></p>');
    }
  }
);

watch(
  () => props.disabled,
  (disabled) => {
    if (!editor || editor.isDestroyed) {
      return;
    }
    if (disabled) {
      editor.disable();
    } else {
      editor.enable();
    }
  }
);

onBeforeUnmount(() => {
  if (editor && !editor.isDestroyed) {
    editor.destroy();
  }
  editor = null;
  toolbar = null;
});
</script>

<template>
  <div class="rich-editor" :class="{ 'is-disabled': disabled, 'is-focused': focused }">
    <div ref="toolbarEl" class="rich-editor-toolbar"></div>
    <div ref="editableEl" class="rich-editor-body"></div>
  </div>
</template>

<style scoped>
.rich-editor {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--surface);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.rich-editor.is-focused {
  border-color: var(--primary-border);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12);
}

.rich-editor.is-disabled {
  opacity: 0.7;
}

.rich-editor-toolbar {
  border-bottom: 1px solid var(--line);
  flex-wrap: wrap;
}

.rich-editor-body {
  min-height: 320px;
  text-align: left;
}

@media (max-width: 640px) {
  .rich-editor-body {
    min-height: 240px;
  }
}
</style>
