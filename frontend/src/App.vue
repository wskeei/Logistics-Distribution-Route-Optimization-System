<template>
  <div id="app" class="font-sans text-slate-700 h-screen flex flex-col overflow-hidden bg-slate-50">
    <template v-if="!isLoginPage">
      <el-container class="h-full">
        <!-- Modern Sidebar -->
        <el-aside width="260px" class="glass-panel h-full flex flex-col transition-all duration-300 z-20 shadow-lg relative">
          <div class="h-20 flex items-center justify-center border-b border-white/40">
            <div class="flex items-center gap-3">
              <!-- Logo Placeholder or Icon -->
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold shadow-md">
                L
              </div>
              <h3 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-light to-accent tracking-tight">物流系统</h3>
            </div>
          </div>
          
          <el-menu
            :default-active="activeMenu"
            class="flex-1 overflow-y-auto px-3 py-6 bg-transparent border-none"
            router
            :text-color="'#475569'" 
            :active-text-color="'#0ea5e9'"
          >
            <div class="mb-2 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Main</div>
            <el-menu-item index="/" class="menu-item-custom">
              <el-icon><HomeFilled /></el-icon>
              <span>仪表盘</span>
            </el-menu-item>
            
            <div class="mt-6 mb-2 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Operations</div>
            <el-menu-item index="/dispatcher" class="menu-item-custom">
              <el-icon><Cpu /></el-icon>
              <span>调度中心</span>
            </el-menu-item>
            <el-menu-item index="/orders" class="menu-item-custom">
              <el-icon><Tickets /></el-icon>
              <span>订单管理</span>
            </el-menu-item>
            <el-menu-item index="/tasks" class="menu-item-custom">
              <el-icon><Finished /></el-icon>
              <span>任务列表</span>
            </el-menu-item>
            
            <div class="mt-6 mb-2 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Resources</div>
            <el-menu-item index="/products" class="menu-item-custom">
              <el-icon><Box /></el-icon>
              <span>货物管理</span>
            </el-menu-item>
            <el-menu-item index="/customers" class="menu-item-custom">
              <el-icon><User /></el-icon>
              <span>客户管理</span>
            </el-menu-item>
            <el-menu-item index="/vehicles" class="menu-item-custom">
              <el-icon><Van /></el-icon>
              <span>车辆管理</span>
            </el-menu-item>
             <el-menu-item index="/depots" class="menu-item-custom">
              <el-icon><OfficeBuilding /></el-icon>
              <span>仓库管理</span>
            </el-menu-item>

            <div class="mt-6 mb-2 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Deprecated</div>
             <el-menu-item index="/planning" class="menu-item-custom">
              <el-icon><Location /></el-icon>
              <span>路径规划 (旧)</span>
            </el-menu-item>
          </el-menu>
          
          <!-- User Profile Brief -->
          <div class="p-4 border-t border-white/40 bg-white/30 backdrop-blur-sm">
             <div class="flex items-center gap-3">
                <el-avatar :size="36" class="bg-primary/20 text-primary font-bold">{{ username.charAt(0).toUpperCase() }}</el-avatar>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-semibold text-slate-700 truncate">{{ username }}</p>
                    <p class="text-xs text-slate-500 truncate">Online</p>
                </div>
                <el-button type="danger" text circle size="small" @click="handleLogout">
                    <el-icon><SwitchButton /></el-icon>
                </el-button>
             </div>
          </div>
        </el-aside>
        
        <el-container class="relative flex flex-col h-full overflow-hidden">
          <!-- Translucent Header -->
          <el-header class="h-20 glass-panel border-b border-white/40 flex items-center justify-between px-8 sticky top-0 z-10 w-full backdrop-blur-md bg-white/50 shadow-sm/5">
            <div class="flex flex-col justify-center">
              <h1 class="text-2xl font-bold text-slate-800 tracking-tight">
                {{ $route.meta.title || getPageTitle($route.path) }}
              </h1>
              <span class="text-xs text-slate-500 font-medium">Logistics Optimization System v1.0</span>
            </div>
            
            <div class="flex items-center gap-4">
               <el-tooltip content="Notifications" placement="bottom">
                   <el-badge is-dot class="cursor-pointer">
                       <el-icon class="text-slate-500 hover:text-primary transition-colors" :size="20"><Bell /></el-icon>
                   </el-badge>
               </el-tooltip>
            </div>
          </el-header>
          
          <el-main class="p-0 overflow-y-auto scroll-smooth bg-slate-50/50">
             <div class="w-full max-w-7xl mx-auto relative min-h-full">
                <router-view v-slot="{ Component }">
                  <transition name="fade-slide">
                    <component :is="Component" />
                  </transition>
                </router-view>
             </div>
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
import { 
    HomeFilled, Cpu, Tickets, Box, User, Van, 
    OfficeBuilding, Finished, Location, SwitchButton, Bell 
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isLoginPage = computed(() => route.name === 'Login')
const username = computed(() => authStore.user?.username || 'User')
const activeMenu = computed(() => route.path)

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const getPageTitle = (path) => {
    const map = {
        '/': '仪表盘 Dashboard',
        '/dispatcher': '调度中心 Dispatcher',
        '/orders': '订单管理 Orders',
        '/products': '货物管理 Products',
        '/customers': '客户管理 Customers',
        '/vehicles': '车辆管理 Vehicles',
        '/depots': '仓库管理 Depots',
        '/tasks': '任务列表 Tasks',
        '/planning': '路径规划 Planning'
    }
    return map[path] || '物流配送系统'
}
</script>

<style scoped>
/* Custom Menu Item Styling */
.menu-item-custom {
    margin: 4px 0;
    border-radius: 12px;
    height: 48px;
    line-height: 48px;
    transition: all 0.2s ease;
    border: 1px solid transparent;
}

.menu-item-custom:hover {
    background-color: rgba(255, 255, 255, 0.6) !important;
    color: var(--color-primary);
    transform: translateX(4px);
}

.menu-item-custom.is-active {
    background: linear-gradient(90deg, rgba(14, 165, 233, 0.1) 0%, rgba(14, 165, 233, 0.05) 100%) !important;
    color: var(--color-primary) !important;
    font-weight: 600;
    border: 1px solid rgba(14, 165, 233, 0.2);
    box-shadow: 0 2px 5px rgba(14, 165, 233, 0.05);
}

.el-menu-item .el-icon {
    transition: transform 0.2s ease;
}
.menu-item-custom:hover .el-icon {
    transform: scale(1.1);
}

/* Page Transition - Simultaneous */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s ease-out;
}

.fade-slide-leave-active {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 10; /* Leave on top */
  pointer-events: none; /* Prevent clicks on leaving element */
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
