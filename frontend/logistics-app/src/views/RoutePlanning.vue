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
            
            <el-form-item label="添加地点">
              <el-cascader
                ref="cascaderRef"
                v-model="cascaderValue"
                :options="addressOptions"
                placeholder="请选择省/市/区"
                style="width: 100%;"
                filterable
                clearable
              />
              <el-input
                v-model="detailAddress"
                placeholder="请输入详细街道地址"
                style="margin-top: 10px;"
                clearable
              />
              <el-button type="success" @click="addLocation" style="width: 100%; margin-top: 10px;" :loading="isGeocoding">
                {{ isGeocoding ? '解析中...' : '添加地点' }}
              </el-button>
            </el-form-item>

            <el-table :data="selectedLocations" stripe style="width: 100%; margin-top: 10px;" max-height="250">
              <el-table-column prop="name" label="地点名称" />
              <el-table-column label="操作" width="80">
                <template #default="scope">
                  <el-button type="danger" size="small" @click="removeLocation(scope.$index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <el-form-item style="margin-top: 20px;">
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
            <p>最短距离: {{ result.total_distance?.toFixed(2) }} km</p>
            <!-- Displaying the first route for simplicity -->
            <p>路径顺序 (第一条): {{ result.routes?.[0]?.join(' -> ') }}</p>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧地图 -->
      <el-col :span="18" class="map-container">
        <Map
          :locations="selectedLocations"
          :task="result"
          @add-location="handleAddNewLocationByClick"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Map from '../components/Map.vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import addressOptionsData from '../assets/pcas-code.json'

// --- State ---
const isLoading = ref(false)
const isGeocoding = ref(false)
const result = ref(null)
const generations = ref(500)
const patience = ref(50)

const cascaderRef = ref(null) // Ref for the cascader component
const addressOptions = ref([])
const cascaderValue = ref([])
const detailAddress = ref('')

const selectedLocations = ref([
  // Add a default depot location for convenience
  { id: 0, name: '上海市, 人民广场', x: 121.4737, y: 31.2304 },
])

onMounted(() => {
  addressOptions.value = addressOptionsData
})

// --- Address Handling ---
const addLocation = async () => {
  const checkedNodes = cascaderRef.value?.getCheckedNodes()
  if (!checkedNodes || checkedNodes.length === 0) {
    ElMessage.warning('请选择省市区')
    return
  }
  if (!detailAddress.value) {
    ElMessage.warning('请输入详细街道地址')
    return
  }

  const [node] = checkedNodes
  const region = node.pathLabels.join(','); // e.g., "上海市,黄浦区"
  const address = detailAddress.value;
  const fullAddress = node.pathLabels.join('') + detailAddress.value;
  
  isGeocoding.value = true;
  
  try {
    const response = await axios.post('/api/geocode/address', {
      address: address,
      region: region
    });
    
    const { x, y } = response.data;

    const newId = selectedLocations.value.length > 0
      ? Math.max(...selectedLocations.value.map(l => l.id)) + 1
      : 1;

    selectedLocations.value.push({
      id: newId,
      name: fullAddress,
      x: x,
      y: y
    });

    ElMessage.success(`地址 "${fullAddress}" 已成功添加并定位！`);

    // Clear inputs
    cascaderValue.value = [];
    detailAddress.value = '';

  } catch (error) {
    console.error('Geocoding failed:', error);
    if (error.response && error.response.data && error.response.data.detail) {
      ElMessage.error(`地址解析失败: ${error.response.data.detail}`);
    } else {
      ElMessage.error('地址解析失败，请检查地址或网络连接');
    }
  } finally {
    isGeocoding.value = false;
  }
}

const removeLocation = (index) => {
  selectedLocations.value.splice(index, 1)
}

// --- Map Interaction ---
const handleAddNewLocationByClick = (newLoc) => {
  const newId = selectedLocations.value.length > 0 
    ? Math.max(...selectedLocations.value.map(l => l.id)) + 1 
    : 1;
    
  selectedLocations.value.push({
    id: newId,
    name: `地图点 #${newId}`,
    x: newLoc.x,
    y: newLoc.y
  })
}

// --- Optimization ---
const startOptimization = async () => {
  if (selectedLocations.value.length < 2) {
    ElMessage.warning('请至少添加一个起点和一个客户点')
    return
  }
  if (selectedLocations.value.length > 50) {
    ElMessage.warning('由于 API 限制，一次最多只能优化 50 个地点')
    return
  }

  isLoading.value = true
  result.value = null

  try {
    const response = await axios.post('/api/optimize', {
      // The backend expects 'locations' with id, x, y
      locations: selectedLocations.value.map(loc => ({ id: loc.id, x: loc.x, y: loc.y })),
      generations: generations.value,
      patience: patience.value,
      // Add a default vehicle capacity for this simple page
      vehicle_capacity: 1000, 
    })
    const apiResult = response.data;
    
    // Manually construct a 'stops' array for the Map component based on the routes
    const stops = [];
    let stopCounter = 1;
    if (apiResult.routes) {
      apiResult.routes.forEach(route => {
        // Skip the depot (usually the first element in the route)
        const customerStops = route.slice(1);
        customerStops.forEach(customerId => {
          const customer = selectedLocations.value.find(loc => loc.id === customerId);
          if (customer) {
            stops.push({
              stop_order: stopCounter++,
              customer: { x: customer.x, y: customer.y }
            });
          }
        });
      });
    }
    
    // Combine apiResult with the manually created stops to form the 'task' object for the map
    result.value = {
      ...apiResult,
      stops: stops
    };
    ElMessage.success('路径优化完成！')
  } catch (error) {
    console.error('优化失败:', error)
    if (error.response && error.response.data && error.response.data.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('优化失败，请检查输入数据或网络连接')
    }
  } finally {
    isLoading.value = false
  }
}
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
  display: flex;
  flex-direction: column;
}

.el-card__body {
  flex-grow: 1;
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