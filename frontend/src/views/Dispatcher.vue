<template>
  <el-row :gutter="20">
    <el-col :span="24">
      <el-card>
        <template #header>调度中心</template>
        <el-steps :active="activeStep" finish-status="success" simple style="margin-bottom: 20px">
          <el-step title="配置" />
          <el-step title="信息" />
          <el-step title="执行" />
          <el-step title="结果" />
        </el-steps>

        <!-- Step 0: 选择资源 -->
        <div v-if="activeStep === 0">
          <el-form label-position="top">
            <el-form-item label="选择出发仓库">
              <el-select v-model="selectedDepot" placeholder="请选择仓库" filterable style="width: 100%">
                <el-option v-for="depot in depots" :key="depot.id" :label="depot.name" :value="depot.id" />
              </el-select>
            </el-form-item>
          </el-form>
          <el-divider />
          <el-row :gutter="20">
            <el-col :span="12">
              <h3>选择待调度订单 (状态为 PENDING)</h3>
              <el-table :data="pendingOrders" @selection-change="handleOrderSelection" height="400">
                <el-table-column type="selection" width="55" />
                <el-table-column prop="customer.name" label="客户" />
                <el-table-column prop="demand" label="需求量" />
                <el-table-column prop="created_at" label="创建时间">
                    <template #default="scope">
                        {{ new Date(scope.row.created_at).toLocaleDateString() }}
                    </template>
                </el-table-column>
              </el-table>
            </el-col>
            <el-col :span="12">
              <h3>选择可用车辆</h3>
              <el-table :data="vehicles" @selection-change="handleVehicleSelection" height="400">
                <el-table-column type="selection" width="55" />
                <el-table-column prop="name" label="车辆名称" />
                <el-table-column prop="capacity" label="容量" />
              </el-table>
            </el-col>
          </el-row>
          <div style="text-align: center; margin-top: 20px;">
            <el-button type="primary" @click="nextStep" :disabled="!selectedDepot || selectedOrders.length === 0 || selectedVehicles.length === 0">
              下一步: 填写信息
            </el-button>
          </div>
        </div>

        <!-- Step 1: 填写信息 -->
        <div v-if="activeStep === 1">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h3>任务信息</h3>
                <el-form label-position="top" :model="taskInfo">
                    <el-form-item label="任务标题" required>
                        <el-input v-model="taskInfo.title" placeholder="例如：2024-05-20 上午配送任务" />
                    </el-form-item>
                    <el-form-item label="任务描述">
                        <el-input v-model="taskInfo.description" type="textarea" :rows="4" placeholder="备注信息..." />
                    </el-form-item>
                </el-form>
                <div style="text-align: center; margin-top: 20px;">
                    <el-button @click="activeStep = 0">上一步</el-button>
                    <el-button type="primary" @click="startDispatch" :disabled="!taskInfo.title">
                        开始调度
                    </el-button>
                </div>
            </div>
        </div>

        <!-- Step 2: 执行中 -->
        <div v-if="activeStep === 2" v-loading="isDispatching" :element-loading-text="dispatchStatus" style="padding: 50px;">
          <el-result icon="info" title="智能调度计算中" :sub-title="dispatchStatus">
          </el-result>
        </div>

        <!-- Step 3: 结果展示 -->
        <div v-if="activeStep === 3">
          <el-result v-if="dispatchResult && !dispatchResult.error" icon="success" title="调度成功" :sub-title="`成功规划 ${dispatchResult.tasks.length} 条路线`">
             <template #extra>
               <el-button type="primary" @click="reset">发起新调度</el-button>
             </template> 
          </el-result>

          <el-alert v-else-if="dispatchResult && dispatchResult.error" title="调度失败" type="error" :description="dispatchResult.error" show-icon />

          <!-- Map Visualization -->
          <div v-if="dispatchResult && !dispatchResult.error" style="height: 600px; margin-top: 20px;">
             <Map :locations="mapLocations" :task="mapTaskData"  />
          </div>
        </div>

      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '../store';
import Map from '../components/Map.vue'; // Reuse Map component

const authStore = useAuthStore();

const activeStep = ref(0);
const depots = ref([]);
const pendingOrders = ref([]);
const vehicles = ref([]);
const selectedDepot = ref(null);
const selectedOrders = ref([]); // Array of full order objects
const selectedVehicles = ref([]);

const taskInfo = ref({
    title: '',
    description: ''
});

const isDispatching = ref(false);
const dispatchStatus = ref('正在初始化...');
const dispatchResult = ref(null);
let pollInterval = null;

// Map Data
const mapLocations = ref([]);
const mapTaskData = ref(null);


const fetchData = async (url) => {
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${authStore.token}` },
  });
  if (!response.ok) throw new Error(`Failed to fetch from ${url}`);
  return response.json();
};

const watchDepotChange = async (newVal) => {
  if (newVal) {
     try {
         // Fetch vehicles for this depot
         vehicles.value = await fetchData(`/api/vehicles/?current_depot_id=${newVal}`);
     } catch (e) {
         ElMessage.error("获取该仓库车辆失败");
         vehicles.value = [];
     }
  } else {
      vehicles.value = [];
  }
};

import { watch } from 'vue';
watch(selectedDepot, watchDepotChange);

onMounted(async () => {
  try {
    const [allOrders, allDepots] = await Promise.all([
      fetchData('/api/orders/'),
      fetchData('/api/depots/'),
    ]);
    pendingOrders.value = allOrders.filter(o => o.status === 'PENDING');
    // vehicles.value = allVehicles; // Removed initial fetch
    depots.value = allDepots;
    
    // Set default title
    const dateStr = new Date().toLocaleDateString();
    taskInfo.value.title = `${dateStr} 配送调度任务`;

  } catch (error) {
    ElMessage.error('获取基础数据失败');
  }
});

const handleOrderSelection = (val) => {
  selectedOrders.value = val;
};

const handleVehicleSelection = (val) => {
  selectedVehicles.value = val;
};

const nextStep = () => {
    activeStep.value = 1;
};

const startDispatch = async () => {
  activeStep.value = 2;
  isDispatching.value = true;
  dispatchStatus.value = '正在发送调度请求...';

  try {
    const response = await fetch('/api/dispatch/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({
        order_ids: selectedOrders.value.map(o => o.id),
        vehicle_ids: selectedVehicles.value.map(v => v.id),
        depot_id: selectedDepot.value,
        title: taskInfo.value.title,
        description: taskInfo.value.description
      }),
    });

    if (response.status !== 202) throw new Error('启动调度任务失败');
    
    const { task_id } = await response.json();
    pollInterval = setInterval(() => pollTaskStatus(task_id), 1000);

  } catch (error) {
    ElMessage.error(error.message);
    activeStep.value = 0; // Go back
    isDispatching.value = false;
  }
};

const pollTaskStatus = async (taskId) => {
  try {
    const response = await fetchData(`/api/dispatch/status/${taskId}`);
    dispatchStatus.value = response.result && typeof response.result === 'string' ? response.result : `任务状态: ${response.status}...`;

    if (response.status === 'Success' || response.status === 'Failed') {
      clearInterval(pollInterval);
      isDispatching.value = false;
      activeStep.value = 3; // Show result
      
      if (response.status === 'Success') {
          dispatchResult.value = response.result;
          prepareMapData(response.result); // Prepare data for map
      } else {
          dispatchResult.value = { error: response.error || 'Unknown error' };
      }
    }
  } catch (error) {
    ElMessage.error('轮询任务状态失败');
    clearInterval(pollInterval);
    activeStep.value = 0;
  }
};

const prepareMapData = (result) => {
    // 1. Prepare Locations (Depot + Customers) for the Map component
    const depot = depots.value.find(d => d.id === selectedDepot.value);
    
    const locs = [];
    // Add Depot
    if (depot) {
        locs.push({ id: depot.id, name: `[仓库] ${depot.name}`, x: depot.x, y: depot.y, type: 'depot' });
    }
    
    // Add Customers from the dispatched orders
    // result.tasks contains the created tasks. Each task has stops.
    // We can extract all unique customers from all tasks.
    
    // However, selectedOrders already contains customer info.
    selectedOrders.value.forEach(order => {
        locs.push({
            id: order.customer.id,
            name: order.customer.name,
            x: order.customer.x,
            y: order.customer.y,
            type: 'customer'
        });
    });
    
    mapLocations.value = locs;

    // 2. Prepare Task Data (Routes) for Map component
    // Map component expects { routes: [[id1, id2...], ...], stops: [...] }
    // The result.tasks contains full Task objects with path_geometries (if integrated) or we need to reconstruct from stops.
    
    // Since backend might not return 'routes' array directly in DispatchResult (it returns list of Tasks),
    // we need to adapt it. 
    // IF the Map component logic relies on `routes` being list of IDs:
    
    const routes = [];
    const stops = [];
    const path_geometries = []; // Add this
    
    result.tasks.forEach(task => {
        // Construct route sequence for this vehicle
        // Typically: Depot -> Stop1 -> Stop2 -> ... -> Depot (implied loop? or just path)
        const taskRoute = [depot.id];
        
        // Collect path geometries if available
        if (task.path_geometries) {
             path_geometries.push(...task.path_geometries);
        }

        // Sort stops by order
        const sortedStops = [...task.stops].sort((a, b) => a.stop_order - b.stop_order);
        
        sortedStops.forEach(stop => {
            taskRoute.push(stop.customer.id);
            // Also collect stops info for markers
             stops.push({
                 stop_order: stop.stop_order, // Global order might be confusing if multiple vehicles, but Map handles it per route if capable
                 customer: { x: stop.customer.x, y: stop.customer.y }
             });
        });
        
        routes.push(taskRoute);
    });

    mapTaskData.value = {
        routes: routes,
        stops: stops,
        path_geometries: path_geometries // Pass to map
    };
};

const reset = () => {
  activeStep.value = 0;
  isDispatching.value = false;
  dispatchResult.value = null;
  selectedDepot.value = null;
  selectedOrders.value = [];
  selectedVehicles.value = [];
  taskInfo.value = { title: '', description: '' };
};
</script>

<style scoped>
/* Steps customization */
:deep(.el-step__title) {
    font-size: 14px;
}
</style>