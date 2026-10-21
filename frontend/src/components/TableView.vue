<template>
  <div class="table-view">
    <el-table :data="rows" border size="small" max-height="300">
      <el-table-column
        v-for="c in columns"
        :key="c"
        :prop="c"
        :label="c"
        show-overflow-tooltip
      />
    </el-table>
    <div v-if="shape && shape[0] > rows.length" class="table-note">
      仅展示前 {{ rows.length }} 行，共 {{ shape[0] }} 行
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  data: { type: Array, default: () => [] },
  shape: { type: Array, default: null },
})

// 值为对象/数组时转成字符串，便于表格展示
const rows = computed(() =>
  props.data.map((row) => {
    const out = {}
    Object.keys(row).forEach((k) => {
      const v = row[k]
      out[k] = typeof v === 'object' ? JSON.stringify(v) : v
    })
    return out
  }),
)
</script>

<style scoped>
.table-view { background: #fff; }
.table-note { font-size: 12px; color: #909399; padding: 4px 8px; }
</style>
