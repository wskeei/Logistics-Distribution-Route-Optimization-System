<template>
  <div id="app" class="font-sans text-slate-800">
    <template v-if="!isLoginPage">
      <el-container class="h-screen overflow-hidden">
        <!-- Glass Sidebar -->
        <el-aside width="240px" class="glass-panel h-full flex flex-col transition-all duration-300">
          <div class="h-16 flex items-center justify-center border-b border-white/20">
            <h3 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">物流系统</h3>
          </div>
          <el-menu
            :default-active="activeMenu"
            class="flex-1 overflow-y-auto bg-transparent border-r-0 pt-4"
            router
            :text-color="'#334155'"
            :active-text-color="'#0EA5E9'"
          >
            <el-menu-item index="/" class="hover:bg-white/30 transition-colors mx-2 rounded-lg my-1">
              <el-icon><HomeFilled /></el-icon>
              <span>仪表盘</span>
            </el-menu-item>
            <el-menu-item index="/dispatcher" class="hover:bg-white/30 transition-colors mx-2 rounded-lg my-1">
              <el-icon><Cpu /></el-icon>
              <span>调度中心</span>
            </el-menu-item>
            <el-menu-item index="/orders" class="hover:bg-white/30 transition-colors mx-2 rounded-lg my-1">
              <el-icon><Tickets /></el-icon>
              <span>订单管理</span>
            </el-menu-item>
            <el-menu-item index="/products" class="hover:bg-white/30 transition-colors mx-2 rounded-lg my-1">
              <el-icon><Box /></el-icon>
              <span>货物管理</span>
            </el-menu-item>
            <el-menu-item index="/customers" class="hover:bg-white/30 transition-colors mx-2 rounded-lg my-1">
              <el-icon><User /></el-icon>
              <span>客户管理</span>
            </el-menu-item>
            <el-menu-item index="/vehicles" class="hover:bg-white/30 transition-colors mx-2 rounded-lg my-1">
              <el-icon><Van /></el-icon>
              <span>车辆管理</span>
            </el-menu-item>
            <el-menu-item index="/depots" class="hover:bg-white/30 transition-colors mx-2 rounded-lg my-1">
              <el-icon><OfficeBuilding /></el-icon>
              <span>仓库管理</span>
            </el-menu-item>
            <el-menu-item index="/tasks" class="hover:bg-white/30 transition-colors mx-2 rounded-lg my-1">
              <el-icon><Finished /></el-icon>
              <span>任务列表</span>
            </el-menu-item>
            <el-menu-item index="/planning" class="hover:bg-white/30 transition-colors mx-2 rounded-lg my-1">
              <el-icon><Location /></el-icon>
              <span>路径规划 (旧)</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-container class="relative">
          <!-- Glass Header -->
          <el-header class="h-16 glass-panel border-b border-white/20 flex items-center justify-between px-6 sticky top-0 z-10 w-full backdrop-blur-md bg-white/30">
            <div class="flex items-center">
              <div class="text-xl font-medium text-slate-700">
                {{ $route.meta.title || '物流配送路径规划系统' }}
              </div>
            </div>
            <div class="flex items-center gap-4">
              <span class="text-sm text-slate-500">欢迎，<span class="font-semibold text-slate-700">{{ username }}</span></span>
              <el-button type="danger" plain size="small" circle @click="handleLogout" class="shadow-md hover:shadow-lg transition-transform hover:-translate-y-0.5">
                <el-icon><SwitchButton /></el-icon>
              </el-button>
            </div>
          </el-header>
          
          <el-main class="p-6 overflow-y-auto scroll-smooth">
            <router-view v-slot="{ Component }">
              <transition
                enter-active-class="animate__animated animate__fadeIn"
                leave-active-class="animate__animated animate__fadeOut"
                mode="out-in"
              >
                <component :is="Component" />
              </transition>
            </router-view>
          </el-main>
        </el-container>
      </el-container>
    </template>
    
    <template v-else>
      <router-view />
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './store'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isLoginPage = computed(() => route.name === 'Login')
const username = computed(() => authStore.user?.username || '用户')
const activeMenu = computed(() => route.path)

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style>
/* Global overrides if needed */
.el-menu {
  border-right: none !important;
}
.el-menu-item.is-active {
  background-color: rgba(14, 165, 233, 0.1) !important;
  font-weight: 600;
}
</style>
