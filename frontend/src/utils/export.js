// 导出工具：对话导出为 Markdown

export function exportMarkdown(messages, datasetName = '') {
  const lines = [`# 数据分析对话记录`, '']
  if (datasetName) {
    lines.push(`> 数据集：${datasetName}`, '')
  }
  lines.push(`> 导出时间：${new Date().toLocaleString('zh-CN')}`, '')
  messages.forEach((m) => {
    if (m.role === 'user') {
      lines.push('', `## 问题`, '', m.content, '')
    } else if (m.role === 'assistant') {
      lines.push('', `## 分析结论`, '', m.content, '')
    }
  })
  const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
  downloadBlob(blob, `analysis_chat_${Date.now()}.md`)
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
