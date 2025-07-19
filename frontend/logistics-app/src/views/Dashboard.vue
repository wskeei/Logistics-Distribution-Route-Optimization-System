<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <h1>物流配送路径规划系统</h1>
        <p class="welcome-text">欢迎回来，{{ username }}！</p>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="dashboard-stats">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" size="40" color="#409EFF"><User /></el-icon>
            <div class="stat-info">
              <div class="stat-number">{{ customerCount }}</div>
              <div class="stat-label">客户总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" size="40" color="#67C23A"><Document /></el-icon>
            <div class="stat-info">
              <div class="stat-number">{{ taskCount }}</div>
              <div class="stat-label">任务总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" size="40" color="#E6A23C"><Check /></el-icon>
            <div class="stat-info">
              <div class="stat-number">{{ completedTaskCount }}</div>
              <div class="stat-label">已完成任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="dashboard-actions">
      <el-col :span="6">
        <el-card class="action-card" @click="navigateTo('/planning')">
          <div class="action-content">
            <el-icon size="48" color="#409EFF"><Location /></el-icon>
            <h3>路径规划</h3>
            <p>智能优化配送路线</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="action-card" @click="navigateTo('/customers')">
          <div class="action-content">
            <el-icon size="48" color="#67C23A"><User /></el-icon>
            <h3>客户管理</h3>
            <p>管理客户信息</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="action-card" @click="navigateTo('/tasks')">
          <div class="action-content">
            <el-icon size="48" color="#E6A23C"><Document /></el-icon>
            <h3>任务管理</h3>
            <p>查看和管理配送任务</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="action-card" @click="handleLogout">
          <div class="action-content">
            <el-icon size="48" color="#F56C6C"><SwitchButton /></el-icon>
            <h3>退出登录</h3>
            <p>安全退出系统</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const customerCount = ref(0)
const taskCount = ref(0)
const completedTaskCount = ref(0)

const username = computed(() => authStore.user?.username || '用户')

const fetchOverviewData = async () => {
  try {
    const [customersRes, tasksRes] = await Promise.all([
      axios.get('/api/customers/'),
      axios.get('/api/tasks/'),
    ])
    customerCount.value = customersRes.data.length
    taskCount.value = tasksRes.data.length
    completedTaskCount.value = tasksRes.data.filter(task => task.status === 'COMPLETED').length
  } catch (error) {
    console.error('获取总览数据失败:', error)
    ElMessage.error('获取数据失败')
  }
}

const navigateTo = (path) => {
  router.push(path)
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
  ElMessage.success('已安全退出')
}

onMounted(() => {
  fetchOverviewData()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

h1 {
  color: #303133;
  margin-bottom: 10px;
}

.welcome-text {
  color: #606266;
  margin-bottom: 30px;
  font-size: 16px;
}

.dashboard-stats {
  margin-bottom: 30px;
}

.stat-card {
  height: 120px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  margin-right: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.dashboard-actions {
  margin-top: 20px;
}

.action-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 200px;
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.action-content {
  text-align: center;
  padding: 20px;
}

.action-content h3 {
  margin: 15px 0 10px;
  color: #303133;
}

.action-content p {
  color: #909399;
  font-size: 14px;
}
</style>