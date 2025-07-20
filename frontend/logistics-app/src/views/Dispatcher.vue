<template>
  <el-row :gutter="20">
    <el-col :span="24">
      <el-card>
        <template #header>调度中心</template>
        <el-steps :active="activeStep" finish-status="success" simple style="margin-bottom: 20px">
          <el-step title="选择仓库、订单与车辆" />
          <el-step title="执行调度" />
          <el-step title="查看结果" />
        </el-steps>

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
                <el-table-column prop="id" label="ID" />
                <el-table-column prop="customer.name" label="客户" />
                <el-table-column prop="demand" label="需求量" />
              </el-table>
            </el-col>
            <el-col :span="12">
              <h3>选择可用车辆</h3>
              <el-table :data="vehicles" @selection-change="handleVehicleSelection" height="400">
                <el-table-column type="selection" width="55" />
                <el-table-column prop="id" label="ID" />
                <el-table-column prop="name" label="车辆名称" />
                <el-table-column prop="capacity" label="容量" />
              </el-table>
            </el-col>
          </el-row>
          <div style="text-align: center; margin-top: 20px;">
            <el-button type="primary" @click="startDispatch" :disabled="!selectedDepot || selectedOrders.length === 0 || selectedVehicles.length === 0">
              开始调度
            </el-button>
          </div>
        </div>

        <div v-if="activeStep === 1" v-loading="isDispatching" :element-loading-text="dispatchStatus">
          <el-result icon="info" title="调度正在进行中..." :sub-title="dispatchStatus">
          </el-result>
        </div>

        <div v-if="activeStep === 2">
          <el-result v-if="dispatchResult" :icon="dispatchResult.error ? 'error' : 'success'" :title="dispatchResult.error ? '调度失败' : '调度成功'" :sub-title="dispatchResult.error || `成功创建 ${dispatchResult.total_tasks_created} 个任务`">
            <template #extra>
              <el-button type="primary" @click="reset">返回</el-button>
            </template>
          </el-result>
        </div>

      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '../store';

const authStore = useAuthStore();

const activeStep = ref(0);
const depots = ref([]);
const pendingOrders = ref([]);
const vehicles = ref([]);
const selectedDepot = ref(null);
const selectedOrders = ref([]);
const selectedVehicles = ref([]);

const isDispatching = ref(false);
const dispatchStatus = ref('正在初始化...');
const dispatchResult = ref(null);
let pollInterval = null;

const fetchData = async (url) => {
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${authStore.token}` },
  });
  if (!response.ok) throw new Error(`Failed to fetch from ${url}`);
  return response.json();
};

onMounted(async () => {
  try {
    const [allOrders, allVehicles, allDepots] = await Promise.all([
      fetchData('/api/orders/'),
      fetchData('/api/vehicles/'),
      fetchData('/api/depots/'),
    ]);
    pendingOrders.value = allOrders.filter(o => o.status === 'PENDING');
    vehicles.value = allVehicles;
    depots.value = allDepots;
  } catch (error) {
    ElMessage.error('获取基础数据失败');
  }
});

const handleOrderSelection = (val) => {
  selectedOrders.value = val.map(item => item.id);
};

const handleVehicleSelection = (val) => {
  selectedVehicles.value = val.map(item => item.id);
};

const startDispatch = async () => {
  activeStep.value = 1;
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
        order_ids: selectedOrders.value,
        vehicle_ids: selectedVehicles.value,
        depot_id: selectedDepot.value,
      }),
    });

    if (response.status !== 202) throw new Error('启动调度任务失败');
    
    const { task_id } = await response.json();
    pollInterval = setInterval(() => pollTaskStatus(task_id), 2000);

  } catch (error) {
    ElMessage.error(error.message);
    reset();
  }
};

const pollTaskStatus = async (taskId) => {
  try {
    const response = await fetchData(`/api/dispatch/status/${taskId}`);
    dispatchStatus.value = `任务状态: ${response.status}...`;

    if (response.status === 'Success' || response.status === 'Failed') {
      clearInterval(pollInterval);
      isDispatching.value = false;
      activeStep.value = 2;
      dispatchResult.value = response;
    }
  } catch (error) {
    ElMessage.error('轮询任务状态失败');
    clearInterval(pollInterval);
    reset();
  }
};

const reset = () => {
  activeStep.value = 0;
  isDispatching.value = false;
  dispatchResult.value = null;
  selectedDepot.value = null;
  selectedOrders.value = [];
  selectedVehicles.value = [];
};
</script>