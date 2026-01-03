<template>
  <div class="vehicles-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>车辆管理</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加车辆
          </el-button>
        </div>
      </template>

      <el-table :data="vehicles" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="车辆名称/编号" />
        <el-table-column prop="capacity" label="运力容量 (kg/m³)" />
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button size="small" type="primary" @click="handleEdit(scope.row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingVehicle ? '编辑车辆' : '添加车辆'"
      width="500px"
    >
      <el-form :model="vehicleForm" label-width="120px">
        <el-form-item label="车辆名称/编号">
          <el-input v-model="vehicleForm.name" placeholder="例如：货车 A01" />
        </el-form-item>
        <el-form-item label="运力容量">
          <el-input-number v-model="vehicleForm.capacity" :min="1" :step="10" controls-position="right" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            {{ editingVehicle ? '更新' : '添加' }}
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
import { Plus } from '@element-plus/icons-vue'

const vehicles = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const submitLoading = ref(false)
const editingVehicle = ref(null)

const vehicleForm = ref({
  name: '',
  capacity: 100.0
})

const fetchVehicles = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/vehicles/')
    vehicles.value = response.data
  } catch (error) {
    console.error('获取车辆列表失败:', error)
    ElMessage.error('获取车辆列表失败')
  } finally {
    loading.value = false
  }
}

const handleEdit = (vehicle) => {
  editingVehicle.value = vehicle
  vehicleForm.value = {
    name: vehicle.name,
    capacity: vehicle.capacity
  }
  showAddDialog.value = true
}

const handleDelete = async (vehicle) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除车辆 "${vehicle.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`/api/vehicles/${vehicle.id}`)
    ElMessage.success('删除成功')
    fetchVehicles()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除车辆失败:', error)
      ElMessage.error('删除车辆失败')
    }
  }
}

const handleSubmit = async () => {
  if (!vehicleForm.value.name) {
    ElMessage.warning('请输入车辆名称')
    return
  }
  
  submitLoading.value = true
  try {
    const payload = {
      name: vehicleForm.value.name,
      capacity: vehicleForm.value.capacity
    }

    if (editingVehicle.value) {
      await axios.put(`/api/vehicles/${editingVehicle.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/api/vehicles/', payload)
      ElMessage.success('添加成功')
    }
    
    showAddDialog.value = false
    fetchVehicles()
    // Reset form
    if (!editingVehicle.value) {
       vehicleForm.value = { name: '', capacity: 100.0 }
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败，车辆名称可能重复。')
  } finally {
    submitLoading.value = false
    editingVehicle.value = null
  }
}

onMounted(() => {
  fetchVehicles()
})
</script>

<style scoped>
.vehicles-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
