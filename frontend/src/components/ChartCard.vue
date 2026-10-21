<template>
  <div class="chart-card">
    <div ref="chartEl" class="chart" :style="{ height }"></div>
    <div class="chart-actions">
      <el-button size="small" text type="primary" @click="exportPng">导出图片</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '320px' },
})

const chartEl = ref(null)
let chart = null

function render() {
  if (!chart && chartEl.value) chart = echarts.init(chartEl.value)
  if (chart && props.option) chart.setOption(props.option, true)
}

function onResize() {
  chart && chart.resize()
}

onMounted(() => {
  render()
  window.addEventListener('resize', onResize)
})

watch(() => props.option, render, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart && chart.dispose()
  chart = null
})

function exportPng() {
  if (!chart) return
  const url = chart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' })
  const a = document.createElement('a')
  a.href = url
  a.download = `chart_${Date.now()}.png`
  a.click()
}
</script>

<style scoped>
.chart-card { border: 1px solid #ebeef5; border-radius: 6px; overflow: hidden; background: #fff; }
.chart { width: 100%; }
.chart-actions { text-align: right; padding: 2px 8px; border-top: 1px solid #f0f0f0; }
</style>
