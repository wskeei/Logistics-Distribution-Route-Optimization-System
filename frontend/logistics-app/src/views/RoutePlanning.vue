<template>
  <div class="route-planning-container">
    <el-row :gutter="20" class="full-height">
      <!-- 左侧控制面板 -->
      <el-col :span="6" class="control-panel">
        <el-card class="control-card">
          <template #header>
            <div class="card-header">
              <span>路径规划设置</span>
            </div>
          </template>
          
          <el-form label-position="top">
            <el-form-item label="迭代次数">
              <el-input-number v-model="generations" :min="100" :max="2000" :step="100" />
            </el-form-item>
            
            <el-form-item label="耐心值">
              <el-input-number v-model="patience" :min="10" :max="200" :step="10" />
            </el-form-item>
            
            <el-form-item label="地点数据">
              <el-input
                v-model="locationsInput"
                type="textarea"
                :rows="8"
                placeholder="格式: id,经度,纬度"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button 
                type="primary" 
                @click="startOptimization" 
                :loading="isLoading"
                style="width: 100%"
              >
                {{ isLoading ? '计算中...' : '开始优化' }}
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="result" class="result-section">
            <h4>优化结果</h4>
            <p>最短距离: {{ result.distance?.toFixed(2) }} km</p>
            <p>路径顺序: {{ result.path?.join(' -> ') }}</p>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧地图 -->
      <el-col :span="18" class="map-container">
        <Map
          :locations="locations"
          :path="result?.path"
          @add-location="handleAddNewLocation"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Map from '../components/Map.vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const locationsInput = ref(
`0,121.4737,31.2304
1,121.45,31.22
2,121.50,31.24
3,121.48,31.20
4,121.52,31.25
5,121.46,31.19`
)
const isLoading = ref(false)
const result = ref(null)
const generations = ref(500)
const patience = ref(50)

// 将文本输入解析为地点对象数组
const locations = computed(() => {
  return locationsInput.value
    .trim()
    .split('\n')
    .map(line => {
      const [id, x, y] = line.split(',').map(Number)
      return { id, x, y }
    })
    .filter(loc => !isNaN(loc.id) && !isNaN(loc.x) && !isNaN(loc.y))
})

const handleAddNewLocation = (newLoc) => {
  const existingIds = locations.value.map(l => l.id)
  const newId = existingIds.length > 0 ? Math.max(...existingIds) + 1 : 0
  locationsInput.value += `\n${newId},${newLoc.x.toFixed(4)},${newLoc.y.toFixed(4)}`
}

const startOptimization = async () => {
  if (locations.value.length < 2) {
    ElMessage.warning('请至少添加一个起点和一个客户点')
    return
  }

  isLoading.value = true
  result.value = null

  try {
    const response = await axios.post('/api/optimize', {
      locations: locations.value,
      generations: generations.value,
      patience: patience.value,
    })
    result.value = response.data
    ElMessage.success('路径优化完成！')
  } catch (error) {
    console.error('优化失败:', error)
    ElMessage.error('优化失败，请检查输入数据或网络连接')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  // 可以在这里添加初始化逻辑
})
</script>

<style scoped>
.route-planning-container {
  height: 100vh;
  padding: 20px;
  background-color: #f5f7fa;
}

.full-height {
  height: 100%;
}

.control-panel {
  height: 100%;
}

.control-card {
  height: 100%;
  overflow-y: auto;
}

.card-header {
  font-size: 16px;
  font-weight: bold;
}

.result-section {
  margin-top: 20px;
  padding: 15px;
  background-color: #f0f9ff;
  border-radius: 4px;
}

.result-section h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.result-section p {
  margin: 5px 0;
  font-size: 14px;
  color: #606266;
}

.map-container {
  height: 100%;
}
</style>