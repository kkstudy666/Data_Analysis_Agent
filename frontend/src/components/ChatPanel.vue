<template>
  <div class="chat-panel">
    <!-- 顶部工具栏 -->
    <div class="chat-header">
      <div class="chat-title">
        <template v-if="dataset">数据集：<b>{{ dataset.name }}</b></template>
        <span v-else class="no-dataset">请先在左侧选择数据集</span>
      </div>
      <div class="chat-tools">
        <el-select
          v-model="provider"
          size="small"
          class="model-select"
          :disabled="streaming"
          placeholder="选择模型"
        >
          <el-option
            v-for="m in modelOptions"
            :key="m.provider"
            :label="m.label"
            :value="m.provider"
            :disabled="!m.available"
          >
            <span>{{ m.label }}</span>
            <span v-if="!m.available" class="opt-hint">（未配置 key）</span>
          </el-option>
        </el-select>
        <el-button size="small" :disabled="!messages.length" @click="exportChat">导出对话</el-button>
        <el-button
          size="small"
          type="primary"
          :disabled="!messages.length || !dataset"
          @click="submitReport"
        >
          生成报告
        </el-button>
      </div>
    </div>

    <!-- 快捷分析指令 -->
    <div class="quick-actions">
      <el-tag
        v-for="q in quickQuestions"
        :key="q"
        class="quick-tag"
        effect="plain"
        @click="quickSend(q)"
      >
        {{ q }}
      </el-tag>
    </div>

    <!-- 消息列表 -->
    <div ref="listRef" class="message-list">
      <el-empty
        v-if="!messages.length"
        description="向数据集提出分析需求，Agent 将自动完成查询 → 执行 → 可视化"
      />
      <MessageItem v-for="m in messages" :key="m.id" :message="m" />
    </div>

    <!-- 输入区 -->
    <div class="input-area">
      <el-input
        v-model="input"
        type="textarea"
        :rows="2"
        placeholder="输入分析需求，例如：各品类销售额占比如何？"
        resize="none"
        @keydown.enter.exact.prevent="send"
      />
      <div class="input-actions">
        <span class="hint">Enter 发送 · Shift+Enter 换行</span>
        <div>
          <el-button v-if="streaming" type="danger" size="small" @click="stop">停止</el-button>
          <el-button v-else type="primary" size="small" :disabled="!canSend" @click="send">发送</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import MessageItem from './MessageItem.vue'
import http, { generateReport as apiGenerateReport, getReportStatus, getModels } from '../api'
import { exportMarkdown, downloadBlob } from '../utils/export'

const props = defineProps({ dataset: Object })

const messages = ref([])
const input = ref('')
const streaming = ref(false)
const listRef = ref(null)
const provider = ref('ollama') // 当前模型提供商：ollama / deepseek
const modelOptions = ref([])
let abortCtrl = null
let uid = 0

const quickQuestions = [
  '各品类销售额占比如何？用饼图展示',
  '月度销售额趋势如何？用折线图展示',
  '各地区销售额对比如何？用柱状图展示',
  '销售额与利润的关系如何？用散点图展示',
]

const canSend = computed(() => !!props.dataset && !!input.value.trim() && !streaming.value)

function scrollToBottom() {
  nextTick(() => {
    if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
  })
}

function quickSend(q) {
  if (!props.dataset) return ElMessage.warning('请先选择数据集')
  input.value = q
  send()
}

function newId() {
  return ++uid
}

async function send() {
  const question = input.value.trim()
  if (!question || !props.dataset || streaming.value) return
  input.value = ''

  // 历史消息：仅携带已完成的文本（不含工具过程），实现多轮上下文
  const history = messages.value
    .filter((m) => m.role === 'user' || (m.role === 'assistant' && m.status === 'done'))
    .map((m) => ({ role: m.role, content: m.content }))

  messages.value.push({ id: newId(), role: 'user', content: question })
  // 用 reactive 包装，确保流式过程中对 msg 的修改能触发 Vue 重渲染
  const msg = reactive({
    id: newId(),
    role: 'assistant',
    content: '',
    codes: [],
    charts: [],
    report: null,
    steps: [],
    status: 'streaming',
  })
  messages.value.push(msg)

  streaming.value = true
  scrollToBottom()

  abortCtrl = new AbortController()
  const ctrl = abortCtrl

  try {
    await fetchEventSource('/api/analysis/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify({ dataset_id: props.dataset.id, question, history, provider: provider.value }),
      signal: ctrl.signal,
      openWhenHidden: true,
      onmessage(ev) {
        if (!ev.data) return
        let data
        try {
          data = JSON.parse(ev.data)
        } catch (e) {
          return
        }
        handleEvent(msg, data)
        scrollToBottom()
      },
      onclose() {
        if (msg.status === 'streaming') msg.status = 'done'
        streaming.value = false
      },
      onerror(err) {
        if (msg.status === 'streaming') msg.status = 'error'
        streaming.value = false
        throw err
      },
    })
  } catch (e) {
    if (msg.status === 'streaming') msg.status = 'error'
    streaming.value = false
  }
}

function handleEvent(msg, data) {
  switch (data.type) {
    case 'thinking':
      msg.content += data.delta || ''
      break
    case 'tool_call':
      handleToolCall(msg, data)
      break
    case 'tool_result':
      handleToolResult(msg, data)
      break
    case 'error':
      msg.status = 'error'
      msg.content += `\n\n⚠ ${data.message}`
      break
    case 'done':
      msg.status = 'done'
      break
  }
}

function handleToolCall(msg, data) {
  if (data.tool === 'code_tool') {
    msg.codes.push({ code: data.code || '', result: null, status: 'running' })
    msg.steps.push({ text: '生成并执行数据分析代码', tool: data.tool })
  } else if (data.tool === 'chart_tool') {
    msg.charts.push({ option: null, title: '', status: 'running' })
    msg.steps.push({ text: '生成可视化图表', tool: data.tool })
  } else if (data.tool === 'metadata_tool') {
    msg.steps.push({ text: '查询数据元数据', tool: data.tool })
  } else if (data.tool === 'report_tool') {
    msg.steps.push({ text: '整合生成分析报告', tool: data.tool })
  }
}

function handleToolResult(msg, data) {
  const out = data.output || {}
  if (data.tool === 'code_tool') {
    const code = msg.codes.find((c) => c.status === 'running') || msg.codes[msg.codes.length - 1]
    if (code) {
      code.result = out
      code.status = out.status === 'success' ? 'success' : 'error'
    }
  } else if (data.tool === 'chart_tool') {
    const chart = msg.charts.find((c) => c.status === 'running') || msg.charts[msg.charts.length - 1]
    if (chart) {
      if (out.status === 'success') chart.option = out.option
      chart.status = out.status || 'error'
    }
  } else if (data.tool === 'report_tool') {
    msg.report = typeof out === 'string' ? out : out.text || ''
  }
}

function stop() {
  abortCtrl && abortCtrl.abort()
  streaming.value = false
}

function exportChat() {
  exportMarkdown(
    messages.value.filter((m) => m.role === 'user' || (m.role === 'assistant' && m.content)),
    props.dataset?.name || '',
  )
  ElMessage.success('对话已导出为 Markdown')
}

async function submitReport() {
  const msgs = messages.value
    .filter((m) => m.role === 'user' || (m.role === 'assistant' && m.content))
    .map((m) => ({ role: m.role, content: m.content }))
  if (!msgs.length) return ElMessage.warning('暂无对话内容')
  try {
    const res = await apiGenerateReport({
      dataset_id: props.dataset.id,
      title: `${props.dataset.name} 分析报告`,
      messages: msgs,
    })
    ElMessage.success('报告生成任务已提交')
    pollReport(res.task_id)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function pollReport(taskId) {
  const timer = setInterval(async () => {
    try {
      const st = await getReportStatus(taskId)
      if (st.status === 'completed') {
        clearInterval(timer)
        ElMessage.success('报告已生成')
        downloadReportFile(taskId)
      }
    } catch (e) {
      /* 继续等待 */
    }
  }, 1500)
}

async function downloadReportFile(taskId) {
  try {
    const blob = await http.get(`/reports/${taskId}/download`, { responseType: 'blob' })
    downloadBlob(blob, `analysis_report_${taskId.slice(0, 8)}.md`)
  } catch (e) {
    ElMessage.error('报告下载失败')
  }
}

// 切换数据集时清空对话
watch(
  () => props.dataset?.id,
  () => {
    messages.value = []
  },
)

async function loadModels() {
  try {
    const res = await getModels()
    modelOptions.value = res.models || []
    // DeepSeek 已配置 key 时默认使用（更快更稳）；否则回退本地 Ollama
    const ds = modelOptions.value.find((m) => m.provider === 'deepseek')
    provider.value = ds && ds.available ? 'deepseek' : 'ollama'
  } catch (e) {
    /* 获取失败时保持默认 ollama */
  }
}

onMounted(loadModels)
</script>

<style scoped>
.chat-panel { display: flex; flex-direction: column; height: 100%; }
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.chat-title { font-size: 15px; color: #303133; }
.no-dataset { color: #909399; }
.chat-tools { display: flex; gap: 8px; align-items: center; }
.model-select { width: 170px; }
.opt-hint { color: #c0c4cc; font-size: 12px; margin-left: 4px; }
.quick-actions { display: flex; flex-wrap: wrap; gap: 8px; padding: 10px 20px; background: #fff; border-bottom: 1px solid #f0f0f0; }
.quick-tag { cursor: pointer; }
.message-list { flex: 1; overflow-y: auto; padding: 16px 20px; }
.input-area { background: #fff; border-top: 1px solid #e4e7ed; padding: 12px 20px; }
.input-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 8px; }
.hint { font-size: 12px; color: #c0c4cc; }
</style>
