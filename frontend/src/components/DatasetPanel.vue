<template>
  <div class="dataset-panel">
    <div class="panel-header">
      <h3>数据集</h3>
      <el-upload
        :show-file-list="false"
        :before-upload="beforeUpload"
        :http-request="doUpload"
        accept=".csv,.xlsx,.xls,.json"
      >
        <el-button type="primary" size="small" :loading="uploading">上传</el-button>
      </el-upload>
    </div>

    <div class="ds-list">
      <div
        v-for="ds in datasets"
        :key="ds.id"
        class="ds-item"
        :class="{ active: selected && selected.id === ds.id }"
        @click="select(ds)"
      >
        <div class="ds-row">
          <span class="ds-name" :title="ds.name">{{ ds.name }}</span>
          <span class="ds-type">{{ ds.file_type }}</span>
        </div>
        <div class="ds-meta">{{ ds.row_count }} 行 · {{ ds.column_count }} 列</div>
        <div class="ds-actions" @click.stop>
          <el-button size="small" text @click="openRename(ds)">重命名</el-button>
          <el-button size="small" text type="danger" @click="remove(ds)">删除</el-button>
        </div>
      </div>
      <el-empty v-if="!datasets.length" description="暂无数据集" :image-size="70" />
    </div>

    <div v-if="selected" class="meta-panel">
      <h4>元数据 & 清洗预检</h4>
      <div v-if="metaLoading" class="meta-loading">加载中...</div>
      <template v-else-if="meta">
        <div class="stat-row">
          <el-tag size="small" type="info">行数 {{ meta.row_count }}</el-tag>
          <el-tag size="small" type="info">列数 {{ meta.column_count }}</el-tag>
          <el-tag v-if="meta.duplicate_count" size="small" type="warning">重复 {{ meta.duplicate_count }}</el-tag>
        </div>
        <el-table :data="meta.columns" size="small" max-height="200" class="meta-table">
          <el-table-column prop="name" label="字段" show-overflow-tooltip />
          <el-table-column prop="dtype" label="类型" width="76" />
          <el-table-column prop="missing" label="缺失" width="52" align="right" />
        </el-table>
        <div v-if="meta.suggestions && meta.suggestions.length" class="suggestions">
          <div v-for="(s, i) in meta.suggestions" :key="i" class="suggest">⚠ {{ s }}</div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listDatasets, uploadDataset, renameDataset, deleteDataset, getDatasetMeta } from '../api'

const props = defineProps({ selected: Object })
const emit = defineEmits(['update:selected'])

const datasets = ref([])
const meta = ref(null)
const metaLoading = ref(false)
const uploading = ref(false)

async function load() {
  try {
    datasets.value = await listDatasets()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function loadMeta(dsId) {
  metaLoading.value = true
  try {
    const res = await getDatasetMeta(dsId)
    meta.value = res.meta_info
  } catch (e) {
    meta.value = null
  } finally {
    metaLoading.value = false
  }
}

function select(ds) {
  emit('update:selected', ds)
  loadMeta(ds.id)
}

// 上传：扩展名 + 大小校验
function beforeUpload(file) {
  const ext = file.name.split('.').pop().toLowerCase()
  if (!['csv', 'xlsx', 'xls', 'json'].includes(ext)) {
    ElMessage.error('仅支持 CSV / Excel / JSON 格式')
    return false
  }
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  return true
}

async function doUpload({ file }) {
  uploading.value = true
  try {
    const ds = await uploadDataset(file)
    ElMessage.success('上传成功')
    await load()
    select(ds)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    uploading.value = false
  }
}

async function openRename(ds) {
  try {
    const { value } = await ElMessageBox.prompt('请输入新名称', '重命名', {
      inputValue: ds.name,
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    await renameDataset(ds.id, value.trim() || ds.name)
    ElMessage.success('已重命名')
    await load()
  } catch (e) {
    /* 取消或错误忽略 */
  }
}

async function remove(ds) {
  try {
    await ElMessageBox.confirm(`确认删除「${ds.name}」？此操作不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteDataset(ds.id)
    ElMessage.success('已删除')
    if (props.selected && props.selected.id === ds.id) {
      emit('update:selected', null)
      meta.value = null
    }
    await load()
  } catch (e) {
    /* 取消忽略 */
  }
}

onMounted(load)
</script>

<style scoped>
.dataset-panel { display: flex; flex-direction: column; height: 100%; }
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
}
.panel-header h3 { margin: 0; font-size: 16px; color: #303133; }
.ds-list { flex: 1; overflow-y: auto; padding: 8px; }
.ds-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 6px;
  background: #fff;
  border: 1px solid #ebeef5;
  transition: all 0.2s;
}
.ds-item:hover { border-color: #409eff; }
.ds-item.active { border-color: #409eff; background: #ecf5ff; }
.ds-row { display: flex; justify-content: space-between; align-items: center; }
.ds-name { font-weight: 600; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ds-type { font-size: 12px; color: #909399; background: #f4f4f5; padding: 1px 6px; border-radius: 3px; }
.ds-meta { font-size: 12px; color: #909399; margin-top: 4px; }
.ds-actions { margin-top: 4px; }
.meta-panel { border-top: 1px solid #e4e7ed; padding: 12px 16px; background: #fff; }
.meta-panel h4 { margin: 0 0 8px; font-size: 14px; color: #303133; }
.stat-row { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.meta-table { width: 100%; }
.suggestions { margin-top: 8px; }
.suggest { font-size: 12px; color: #e6a23c; line-height: 1.6; }
.meta-loading { text-align: center; color: #909399; font-size: 13px; padding: 12px; }
</style>
