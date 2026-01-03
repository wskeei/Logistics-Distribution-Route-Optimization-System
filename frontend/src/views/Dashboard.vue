<template>
  <div class="p-6 min-h-full">
    <div class="mb-8" v-motion-slide-visible-once-top>
      <h1 class="text-3xl font-bold text-slate-800 mb-2">物流配送路径规划系统</h1>
      <p class="text-slate-500">欢迎回来，<span class="font-semibold text-primary">{{ username }}</span>！</p>
    </div>

    <!-- Stats Row -->
    <el-row :gutter="24" class="mb-8" v-motion-slide-visible-once-bottom :delay="100">
      <el-col :span="8" v-for="(stat, index) in stats" :key="index">
        <div 
          class="glass-card p-6 flex items-center transition-transform duration-300 hover:translate-y-[-5px] hover:shadow-2xl"
        >
          <div :class="`p-4 rounded-xl bg-${stat.color}-100 text-${stat.color}-500 mr-5`">
            <el-icon :size="32">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <div>
            <div class="text-3xl font-bold text-slate-800 mb-1">{{ stat.value }}</div>
            <div class="text-sm font-medium text-slate-500">{{ stat.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Actions Row -->
    <h2 class="text-xl font-bold text-slate-800 mb-6" v-motion-slide-visible-once-left :delay="200">快速操作</h2>
    <el-row :gutter="24" v-motion-slide-visible-once-bottom :delay="300">
      <el-col :span="6" v-for="(action, index) in actions" :key="index">
        <div 
          class="glass-card p-6 text-center cursor-pointer transition-all duration-300 hover:translate-y-[-5px] hover:shadow-2xl group flex flex-col items-center justify-center h-full min-h-[180px]"
          @click="action.handler"
        >
          <div 
            class="mb-4 p-4 rounded-full bg-slate-50 transition-colors group-hover:bg-primary/10"
          >
            <el-icon :size="40" :class="`text-${action.color}-500 transition-transform group-hover:scale-110 duration-300`">
              <component :is="action.icon" />
            </el-icon>
          </div>
          <h3 class="text-lg font-bold text-slate-700 mb-2 group-hover:text-primary transition-colors">{{ action.title }}</h3>
          <p class="text-sm text-slate-500">{{ action.desc }}</p>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
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

// Data for iteration to keep template clean
const stats = computed(() => [
  { label: '客户总数', value: customerCount.value, icon: 'User', color: 'blue' }, // Tailwind blue
  { label: '任务总数', value: taskCount.value, icon: 'Document', color: 'emerald' }, // Tailwind emerald
  { label: '已完成任务', value: completedTaskCount.value, icon: 'Check', color: 'amber' } // Tailwind amber
])

const actions = [
  { 
    title: '路径规划', 
    desc: '智能优化配送路线', 
    icon: 'Location', 
    color: 'blue',
    handler: () => router.push('/planning')
  },
  { 
    title: '客户管理', 
    desc: '管理客户信息', 
    icon: 'User', 
    color: 'emerald',
    handler: () => router.push('/customers')
  },
  { 
    title: '任务管理', 
    desc: '查看和管理配送任务', 
    icon: 'Document', 
    color: 'amber',
    handler: () => router.push('/tasks')
  },
  { 
    title: '退出登录', 
    desc: '安全退出系统', 
    icon: 'SwitchButton', 
    color: 'red',
    handler: () => {
      authStore.logout()
      router.push('/login')
      ElMessage.success('已安全退出')
    }
  }
]

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
    // ElMessage.error('获取数据失败') // Suppress error on init if backend is down/auth failed
  }
}

onMounted(() => {
  fetchOverviewData()
})
</script>

<style scoped>
/* No scoped styles needed - using Tailwind utility classes */
</style>