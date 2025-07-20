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

      <el-table :data="tasks" style="width: 100%" v-loading="loading">
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
            <el-button 
              size="small" 
              :type="scope.row.status === 'COMPLETED' ? 'warning' : 'success'"
              @click="toggleStatus(scope.row)"
            >
              {{ scope.row.status === 'COMPLETED' ? '标记未完成' : '标记完成' }}
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const tasks = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const submitLoading = ref(false)

const taskForm = ref({
  title: '',
  description: ''
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

const handleSubmit = async () => {
  if (!taskForm.value.depot_id) {
    ElMessage.warning('请选择一个仓库');
    return;
  }
  if (taskForm.value.customer_ids.length === 0) {
    ElMessage.warning('请至少选择一个客户');
    return;
  }

  submitLoading.value = true;
  try {
    // 注意：后端接口是 /api/tasks/optimize
    await axios.post('/api/tasks/optimize', taskForm.value);
    
    ElMessage.success('任务创建和优化成功！');
    showAddDialog.value = false;
    taskForm.value = { depot_id: null, customer_ids: [] }; // 重置表单
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
</style>