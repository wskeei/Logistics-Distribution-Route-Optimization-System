<template>
  <div id="main-layout">
    <div class="sidebar">
      <h2>系统仪表盘</h2>
      <p>欢迎回来，{{ username }}！</p>
      
      <nav class="dashboard-nav">
        <ul>
          <li><router-link to="/customers">客户管理</router-link></li>
          <li><router-link to="/tasks">任务管理</router-link></li>
          <!-- 未来可以添加仓库和车辆管理 -->
          <!-- <li><router-link to="/depots">仓库管理</router-link></li> -->
          <!-- <li><router-link to="/vehicles">车辆管理</router-link></li> -->
        </ul>
      </nav>

      <div class="overview-panel">
        <h3>系统总览</h3>
        <p>客户总数: {{ customerCount }}</p>
        <p>任务总数: {{ taskCount }}</p>
        <p>已完成任务: {{ completedTaskCount }}</p>
      </div>

      <button @click="handleLogout" class="logout-button">登出</button>
    </div>
    
    <!-- 保留地图作为可视化展示 -->
    <Map
      class="map-content"
      :locations="locations"
      :path="result?.path"
      @add-location="handleAddNewLocation"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import Map from '../components/Map.vue';
import { useAuthStore } from '../store';
import axios from 'axios';

const locationsInput = ref(
`0,121.4737,31.2304
1,121.45,31.22
2,121.50,31.24
3,121.48,31.20
4,121.52,31.25
5,121.46,31.19`
);
const isLoading = ref(false);
const result = ref(null);
const generations = ref(500);
const patience = ref(50);

const customerCount = ref(0);
const taskCount = ref(0);
const completedTaskCount = ref(0);

const router = useRouter();
const authStore = useAuthStore();

const username = computed(() => authStore.user?.username || '用户');

// 将文本输入解析为地点对象数组
const locations = computed(() => {
  return locationsInput.value
    .trim()
    .split('\n')
    .map(line => {
      const [id, x, y] = line.split(',').map(Number);
      return { id, x, y };
    })
    .filter(loc => !isNaN(loc.id) && !isNaN(loc.x) && !isNaN(loc.y));
});

const handleAddNewLocation = (newLoc) => {
  const existingIds = locations.value.map(l => l.id);
  const newId = existingIds.length > 0 ? Math.max(...existingIds) + 1 : 0;
  locationsInput.value += `\n${newId},${newLoc.x.toFixed(4)},${newLoc.y.toFixed(4)}`;
};

const startOptimization = async () => {
  if (locations.value.length < 2) {
    alert('请至少添加一个起点和一个客户点。');
    return;
  }

  isLoading.value = true;
  result.value = null;

  try {
    const response = await axios.post('/api/optimize', {
      locations: locations.value,
      generations: generations.value,
      patience: patience.value,
    });
    result.value = response.data;
  } catch (error) {
    console.error('优化失败:', error);
    alert('优化失败，请检查输入数据或网络连接。');
  } finally {
    isLoading.value = false;
  }
};

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};

const fetchOverviewData = async () => {
  try {
    const [customersRes, tasksRes] = await Promise.all([
      axios.get('/api/customers/'),
      axios.get('/api/tasks/'),
    ]);
    customerCount.value = customersRes.data.length;
    taskCount.value = tasksRes.data.length;
    completedTaskCount.value = tasksRes.data.filter(task => task.status === 'COMPLETED').length;
  } catch (error) {
    console.error('获取总览数据失败:', error);
  }
};

onMounted(() => {
  fetchOverviewData();
});
</script>

<style scoped>
#main-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 300px;
  background-color: #f4f4f4;
  padding: 20px;
  box-shadow: 2px 0 5px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sidebar h2, .sidebar h3 {
  margin-top: 0;
}

.dashboard-nav ul {
  list-style: none;
  padding: 0;
}

.dashboard-nav li {
  margin-bottom: 10px;
}

.dashboard-nav a {
  text-decoration: none;
  color: #007bff;
  font-weight: bold;
}

.dashboard-nav a:hover {
  text-decoration: underline;
}

.overview-panel {
  border-top: 1px solid #ccc;
  padding-top: 15px;
}

.logout-button {
  margin-top: auto;
  padding: 10px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button:hover {
  background-color: #c82333;
}

.map-content {
  flex-grow: 1;
  height: 100%;
}
</style>