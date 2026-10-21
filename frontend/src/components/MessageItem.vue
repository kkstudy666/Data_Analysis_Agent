<template>
  <div class="message" :class="message.role">
    <!-- 用户消息：右侧气泡 -->
    <div v-if="message.role === 'user'" class="user-bubble">{{ message.content }}</div>

    <!-- 助手消息：混合内容 -->
    <div v-else class="assistant-wrap">
      <div ref="contentRef" class="assistant-content-box">
        <!-- 思考步骤（可折叠） -->
        <div v-if="message.steps.length" class="steps">
          <el-collapse>
            <el-collapse-item :title="`分析过程（${message.steps.length} 步）`">
              <div v-for="(s, i) in message.steps" :key="i" class="step">• {{ s.text }}</div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 文本结论（markdown） -->
        <div v-if="message.content" class="assistant-content" v-html="renderMarkdown(message.content)"></div>

        <!-- 代码 + 执行结果 -->
        <div v-for="(c, i) in message.codes" :key="'code' + i" class="code-section">
          <CodeBlock :code="c.code" lang="python" />
          <div v-if="c.status === 'running'" class="running"><el-icon class="is-loading"><Loading /></el-icon> 执行中...</div>
          <div v-else-if="c.result" class="code-result">
            <div v-if="c.result.status === 'error'" class="error-text">❌ {{ c.result.error }}</div>
            <template v-else>
              <TableView
                v-if="c.result.result && c.result.result.type === 'dataframe'"
                :columns="c.result.result.columns"
                :data="c.result.result.data"
                :shape="c.result.result.shape"
              />
              <div v-else-if="c.result.result && c.result.result.type === 'scalar'" class="scalar">
                结果 = {{ c.result.result.value }}
              </div>
              <pre v-else-if="c.result.result && c.result.result.type" class="json-view">{{ JSON.stringify(c.result.result, null, 2) }}</pre>
              <pre v-if="c.result.stdout" class="stdout">{{ c.result.stdout }}</pre>
            </template>
          </div>
        </div>

        <!-- 图表 -->
        <ChartCard
          v-for="(ch, i) in message.charts.filter((x) => x.option)"
          :key="'chart' + i"
          :option="ch.option"
        />

        <!-- 报告 -->
        <div v-if="message.report" class="report">
          <div class="report-text" v-html="renderMarkdown(message.report)"></div>
          <el-button size="small" type="primary" @click="downloadReport">下载 Markdown 报告</el-button>
        </div>

        <!-- 流式状态 -->
        <div v-if="message.status === 'streaming'" class="streaming-hint">
          <el-icon class="is-loading"><Loading /></el-icon> 正在分析...
        </div>
        <div v-if="message.status === 'error' && !message.content && !message.codes.length" class="error-text">
          分析失败
        </div>
      </div>

      <div class="assistant-actions">
        <el-button size="small" text @click="exportImage">导出图片</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { marked } from 'marked'
import { Loading } from '@element-plus/icons-vue'
import html2canvas from 'html2canvas'
import { ElMessage } from 'element-plus'
import CodeBlock from './CodeBlock.vue'
import ChartCard from './ChartCard.vue'
import TableView from './TableView.vue'
import { downloadBlob } from '../utils/export'

const props = defineProps({ message: { type: Object, required: true } })
const contentRef = ref(null)

function renderMarkdown(text) {
  try {
    return marked.parse(text || '')
  } catch (e) {
    return String(text)
  }
}

async function exportImage() {
  if (!contentRef.value) return
  try {
    const canvas = await html2canvas(contentRef.value, {
      useCORS: true,
      backgroundColor: '#ffffff',
      scale: 2,
    })
    const a = document.createElement('a')
    a.href = canvas.toDataURL('image/png')
    a.download = `analysis_${Date.now()}.png`
    a.click()
  } catch (e) {
    ElMessage.error('导出图片失败')
  }
}

function downloadReport() {
  const blob = new Blob([props.message.report], { type: 'text/markdown;charset=utf-8' })
  downloadBlob(blob, `report_${Date.now()}.md`)
}
</script>

<style scoped>
.message { display: flex; margin-bottom: 16px; }
.message.user { justify-content: flex-end; }
.user-bubble {
  max-width: 70%;
  background: #409eff;
  color: #fff;
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
.assistant-wrap { max-width: 92%; width: 92%; }
.assistant-content-box { background: #fff; border-radius: 8px; padding: 12px 16px; border: 1px solid #ebeef5; }
.steps { margin-bottom: 8px; }
.step { font-size: 13px; color: #909399; line-height: 1.8; }
.assistant-content { line-height: 1.7; color: #303133; font-size: 14px; }
.assistant-content :deep(h1), .assistant-content :deep(h2), .assistant-content :deep(h3) { margin: 12px 0 6px; }
.assistant-content :deep(pre) { background: #f6f8fa; padding: 12px; border-radius: 6px; overflow-x: auto; }
.assistant-content :deep(table) { border-collapse: collapse; margin: 8px 0; }
.assistant-content :deep(th), .assistant-content :deep(td) { border: 1px solid #e4e7ed; padding: 6px 10px; }
.code-section { margin-top: 10px; }
.code-result { margin-top: 8px; }
.running { font-size: 13px; color: #409eff; margin-top: 6px; display: flex; align-items: center; gap: 4px; }
.error-text { color: #f56c6c; font-size: 13px; margin-top: 6px; }
.scalar { font-size: 14px; color: #303133; padding: 8px; background: #f0f9eb; border-radius: 6px; }
.json-view { background: #f6f8fa; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 12px; }
.stdout { background: #0f172a; color: #e2e8f0; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 12px; }
.report { margin-top: 10px; border-top: 1px dashed #e4e7ed; padding-top: 10px; }
.report-text { margin-bottom: 8px; }
.streaming-hint { font-size: 13px; color: #409eff; margin-top: 8px; display: flex; align-items: center; gap: 4px; }
.assistant-actions { text-align: right; margin-top: 2px; }
</style>
