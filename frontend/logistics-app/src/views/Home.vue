<template>
  <div id="main-layout">
    <div class="sidebar">
      <h2>控制面板</h2>
      
      <div class="control-group">
        <label for="locations-input">客户点坐标 (id,x,y 每行一个):</label>
        <textarea id="locations-input" v-model="locationsInput" rows="10"></textarea>
      </div>

      <div class="control-group">
        <label for="generations-input">最大迭代代数:</label>
        <input type="number" id="generations-input" v-model.number="generations" />
      </div>

      <div class="control-group">
        <label for="patience-input">收敛耐心值 (Patience):</label>
        <input type="number" id="patience-input" v-model.number="patience" />
      </div>
      
      <button @click="startOptimization" :disabled="isLoading">
        {{ isLoading ? '计算中...' : '开始优化' }}
      </button>

      <button @click="handleLogout" class="logout-button">登出</button>
      
      <div v-if="result" class="result-panel">
        <h3>优化结果:</h3>
        <p><strong>路径:</strong> {{ result.path.join(' -> ') }}</p>
        <p><strong>总距离:</strong> {{ result.distance.toFixed(2) }}</p>
      </div>
    </div>
    <Map
      class="map-content"
      :locations="locations"
      :path="result?.path"
      @add-location="handleAddNewLocation"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import Map from '../components/Map.vue';
import { useAuthStore } from '../store';

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

const router = useRouter();
const authStore = useAuthStore();

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
  // 生成一个新的、唯一的ID
  const existingIds = locations.value.map(l => l.id);
  const newId = existingIds.length > 0 ? Math.max(...existingIds) + 1 : 1;
  
  const newLocationString = `\n${newId},${newLoc.x.toFixed(5)},${newLoc.y.toFixed(5)}`;
  
  // 追加到文本框
  locationsInput.value += newLocationString;
  
  alert(`已添加新客户点 ${newId}！`);
};

const startOptimization = async () => {
  if (locations.value.length < 2) {
    alert("请输入至少两个地点（包括起点）。");
    return;
  }
  
  isLoading.value = true;
  result.value = null;

  try {
    const response = await fetch('/api/optimize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({
        locations: locations.value,
        // 可以在这里添加其他参数的输入框
        population_size: 100,
        generations: generations.value,
        patience: patience.value,
        crossover_rate: 0.85,
        mutation_rate: 0.02,
      }),
    });

    if (response.status === 401) {
      // Token expired or invalid, redirect to login
      authStore.logout();
      return;
    }
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    result.value = await response.json();

  } catch (error) {
    console.error("优化请求失败:", error);
    alert("优化请求失败，请检查后端服务是否运行或查看控制台日志。");
  } finally {
    isLoading.value = false;
  }
};

const handleLogout = () => {
  authStore.logout();
};
</script>

<style>
#main-layout {
  display: flex;
  width: 100%;
  height: 100%;
}

.sidebar {
  width: 300px;
  padding: 20px;
  box-shadow: 2px 0 5px rgba(0,0,0,0.1);
  z-index: 1000;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.control-group {
  display: flex;
  flex-direction: column;
}

textarea, input[type="number"] {
  width: 100%;
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box; /* 确保padding不会撑大宽度 */
}

button {
  padding: 10px 15px;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button {
  background-color: #dc3545;
}

button:disabled {
  background-color: #ccc;
}

.result-panel {
  margin-top: 20px;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
}

.map-content {
  flex-grow: 1;
  height: 100%;
}
</style>