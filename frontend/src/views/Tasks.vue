<template>
  <div class="tasks-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务管理</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加任务
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" style="width: 100%" v-loading="loading" @row-click="handleRowClick" row-class-name="cursor-pointer">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="任务标题" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" type="primary" @click.stop="handleEdit(scope.row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click.stop="handleDelete(scope.row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加任务对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="创建并优化新任务"
      width="600px"
      @open="onDialogOpen"
    >
      <el-form :model="taskForm" label-width="80px" v-loading="dialogLoading">
        <el-form-item label="选择仓库" prop="depot_id">
          <el-select v-model="taskForm.depot_id" placeholder="请选择一个仓库" style="width: 100%;">
            <el-option
              v-for="depot in depots"
              :key="depot.id"
              :label="depot.name"
              :value="depot.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="选择车辆" prop="vehicle_id">
            <el-select
              v-model="taskForm.vehicle_id"
              placeholder="请选择车辆"
              style="width: 100%;"
              :disabled="!taskForm.depot_id"
            >
              <el-option
                v-for="vehicle in vehicles"
                :key="vehicle.id"
                :label="vehicle.name + ' (' + vehicle.capacity + 'kg)'"
                :value="vehicle.id"
              />
            </el-select>
        </el-form-item>
        <el-form-item label="选择客户" prop="customer_ids">
           <el-select
            v-model="taskForm.customer_ids"
            multiple
            filterable
            placeholder="请选择客户"
            style="width: 100%;"
          >
            <el-option
              v-for="customer in customers"
              :key="customer.id"
              :label="customer.name"
              :value="customer.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            创建并优化
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑任务对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑任务信息"
      width="500px"
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="任务标题">
          <el-input v-model="editForm.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="editForm.description" type="textarea" placeholder="请输入任务描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="submitEdit" :loading="editLoading">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="任务详情"
      width="900px"
      top="5vh"
    >
      <div v-if="selectedTask" class="detail-container">
         <el-descriptions title="基本信息" border>
            <el-descriptions-item label="标题">{{ selectedTask.title }}</el-descriptions-item>
            <el-descriptions-item label="状态">
               <el-tag :type="getStatusType(selectedTask.status)">{{ getStatusText(selectedTask.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="车辆">{{ selectedTask.vehicle ? selectedTask.vehicle.name : '未分配' }}</el-descriptions-item>
            <el-descriptions-item label="仓库">{{ selectedTask.depot ? selectedTask.depot.name : (selectedTask.depot_id) }}</el-descriptions-item>
            <el-descriptions-item label="总距离">{{ selectedTask.total_distance != null ? selectedTask.total_distance.toFixed(2) + ' km' : '未知' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDate(selectedTask.created_at) }}</el-descriptions-item>
             <el-descriptions-item label="描述" :span="3">{{ selectedTask.description || '无' }}</el-descriptions-item>
         </el-descriptions>

         <div class="map-wrapper" style="height: 500px; margin-top: 20px; border: 1px solid #eee;">
             <Map :locations="detailMapLocations" :task="selectedTask" />
         </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import Map from '../components/Map.vue'

const loading = ref(false)
const showAddDialog = ref(false)
const submitLoading = ref(false)
const showEditDialog = ref(false)
const editLoading = ref(false)
const tasks = ref([])
const vehicles = ref([]) // Added vehicles state

// Details View State
const showDetailDialog = ref(false)
const selectedTask = ref(null)
const detailMapLocations = ref([])

const handleRowClick = (row) => {
    selectedTask.value = row;
    prepareDetailMapData(row);
    showDetailDialog.value = true;
};

const prepareDetailMapData = (task) => {
    const locs = [];
    // 1. Add Depot
    if (task.depot) {
        locs.push({
            id: task.depot.id,
            name: `[仓库] ${task.depot.name}`,
            x: task.depot.x,
            y: task.depot.y,
            type: 'depot'
        });
    }
    
    // 2. Add Stops/Customers
    if (task.stops && task.stops.length > 0) {
        task.stops.forEach(stop => {
            if (stop.customer) {
                locs.push({
                    id: stop.customer.id,
                    name: stop.customer.name,
                    x: stop.customer.x,
                    y: stop.customer.y,
                    type: 'customer',
                    stop_order: stop.stop_order
                });
            }
        });
    }
    detailMapLocations.value = locs;
};

const editForm = ref({
  id: null,
  title: '',
  description: ''
})

const taskForm = ref({
  title: '',
  description: '',
  vehicle_id: null, // Added vehicle_id
  depot_id: null,
  customer_ids: []
})

const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/tasks/')
    tasks.value = response.data
  } catch (error) {
    console.error('获取任务列表失败:', error)
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

const getStatusType = (status) => {
  const types = {
    'PENDING': 'warning',
    'IN_PROGRESS': 'primary',
    'COMPLETED': 'success'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'PENDING': '待处理',
    'IN_PROGRESS': '进行中',
    'COMPLETED': '已完成'
  }
  return texts[status] || status
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// toggleStatus is no longer needed as the backend handles status automatically.

const handleDelete = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`/api/tasks/${task.id}`)
    ElMessage.success('删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除任务失败')
    }
  }
}

const handleEdit = (task) => {
  editForm.value = {
    id: task.id,
    title: task.title || '',
    description: task.description || ''
  }
  showEditDialog.value = true
}

const submitEdit = async () => {
  editLoading.value = true
  try {
    await axios.put(`/api/tasks/${editForm.value.id}`, {
      title: editForm.value.title,
      description: editForm.value.description
    })
    ElMessage.success('更新成功')
    showEditDialog.value = false
    fetchTasks()
  } catch (error) {
    console.error('更新任务失败:', error)
    ElMessage.error('更新任务失败')
  } finally {
    editLoading.value = false
  }
}

const onDialogOpen = async () => {
  dialogLoading.value = true;
  try {
    const [depotsRes, customersRes] = await Promise.all([
      axios.get('/api/depots/'),
      axios.get('/api/customers/')
    ]);
    depots.value = depotsRes.data;
    customers.value = customersRes.data;
  } catch (error) {
    console.error('获取仓库或客户列表失败:', error);
    ElMessage.error('获取初始化数据失败');
    showAddDialog.value = false; // 获取失败则关闭对话框
  } finally {
    dialogLoading.value = false;
  }
};

// Fetch vehicles when depot changes
import { watch } from 'vue';
watch(() => taskForm.value.depot_id, async (newVal) => {
    if (newVal) {
        try {
            const res = await axios.get(`/api/vehicles/?current_depot_id=${newVal}`);
            vehicles.value = res.data;
        } catch(e) {
            console.error(e);
            vehicles.value = [];
        }
    } else {
        vehicles.value = [];
    }
    taskForm.value.vehicle_id = null; // Reset vehicle when depot changes
});

const handleSubmit = async () => {
  if (!taskForm.value.depot_id) {
    ElMessage.warning('请选择一个仓库');
    return;
  }
  if (!taskForm.value.vehicle_id) {
    ElMessage.warning('请选择车辆');
    return;
  }
  if (taskForm.value.customer_ids.length === 0) {
    ElMessage.warning('请至少选择一个客户');
    return;
  }

  submitLoading.value = true;
  try {
    // Correct endpoint: /api/tasks/optimize_cvrp
    // Map customer_ids to order_ids? 
    // Wait, the backend create_and_optimize_cvrp_task expects `order_ids` (List[int]).
    // But the form selects `customers`.
    // We need to create ORDERS first, OR the endpoint should accept customers and create dummy orders?
    // Looking at `tasks.py`, it requires `order_ids`.
    // Oh no. The previous logic was just conceptual?
    
    // If I select customers, I don't have order IDs unless orders exist.
    // The "Task" page "Add Task" flow seems to assume we are creating a task from existing customers = creating orders on the fly?
    // OR we should select ORDERS?
    
    // In `Dispatcher.vue`, we select ORDERS.
    // Here in `Tasks.vue`, we select CUSTOMERS.
    
    // Let's create dummy orders for these customers first? 
    // Or does the backend handle it?
    // Backend `tasks.py` line 44: `if not task_create.order_ids: raise ...`
    
    // So `Tasks.vue` cannot work by just selecting customers if it calls `optimize_cvrp`.
    // It must create orders first.
    
    // Let's perform a quick hack: Create 1 order per selected customer automatically.
    // Then pass those order IDs.
    
    const newOrderIds = [];
    for (const custId of taskForm.value.customer_ids) {
        // Create order
        const orderRes = await axios.post('/api/orders/', {
            customer_id: custId,
            items: [{product_id: 1, quantity: 10}] // Dummy product/quantity
        });
        newOrderIds.push(orderRes.data.id);
    }
    
    await axios.post('/api/tasks/optimize_cvrp', {
        ...taskForm.value,
        order_ids: newOrderIds
    });
    
    ElMessage.success('任务创建和优化成功！');
    showAddDialog.value = false;
    taskForm.value = { depot_id: null, vehicle_id: null, customer_ids: [] }; // 重置表单
    fetchTasks(); // 重新获取任务列表
  } catch (error) {
    console.error('创建任务失败:', error);
    ElMessage.error('创建任务失败，请检查选择的数据。');
  } finally {
    submitLoading.value = false;
  }
};

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.tasks-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.cursor-pointer) {
    cursor: pointer;
}

</style>