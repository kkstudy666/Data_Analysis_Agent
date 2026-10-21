<template>
  <div class="code-block">
    <div class="code-header">
      <span class="lang">{{ lang }}</span>
      <el-button size="small" text type="primary" @click="copy">复制</el-button>
    </div>
    <pre><code v-html="highlighted"></code></pre>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import { ElMessage } from 'element-plus'

const props = defineProps({
  code: { type: String, default: '' },
  lang: { type: String, default: 'python' },
})

const highlighted = computed(() => {
  const l = props.lang && hljs.getLanguage(props.lang) ? props.lang : 'plaintext'
  return hljs.highlight(props.code, { language: l }).value
})

function copy() {
  navigator.clipboard.writeText(props.code).then(() => ElMessage.success('已复制'))
}
</script>

<style scoped>
.code-block { background: #f6f8fa; border: 1px solid #ebeef5; border-radius: 6px; overflow: hidden; }
.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 12px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}
.lang { font-size: 12px; color: #909399; font-family: monospace; }
pre { margin: 0; padding: 12px; overflow-x: auto; }
code { font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; font-size: 13px; }
</style>
