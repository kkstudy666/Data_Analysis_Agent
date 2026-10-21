<template>
  <div class="home">
    <el-container class="full">
      <el-header class="header">
        <div class="brand">📊 智能数据分析 Agent</div>
        <div class="user">
          <span class="username">{{ auth.user?.username }}</span>
          <el-button size="small" @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-container class="body">
        <el-aside width="360px" class="aside">
          <DatasetPanel v-model:selected="selectedDataset" />
        </el-aside>
        <el-main class="main">
          <ChatPanel :dataset="selectedDataset" />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import DatasetPanel from '../components/DatasetPanel.vue'
import ChatPanel from '../components/ChatPanel.vue'

const router = useRouter()
const auth = useAuthStore()
const selectedDataset = ref(null)

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.home, .full { height: 100%; }
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.brand { font-size: 18px; font-weight: 600; color: #303133; }
.user { display: flex; align-items: center; gap: 12px; }
.username { color: #606266; font-size: 14px; }
.body { height: calc(100% - 60px); }
.aside {
  border-right: 1px solid #e4e7ed;
  background: #fafafa;
  overflow-y: auto;
}
.main { padding: 0; background: #f5f7fa; }
</style>
