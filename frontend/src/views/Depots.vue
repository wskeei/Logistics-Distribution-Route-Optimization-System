<template>
  <div class="depots-container p-6 md:p-8">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>仓库管理</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加仓库
          </el-button>
        </div>
      </template>

      <el-table :data="depots" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="仓库名称" />
        <el-table-column prop="address" label="地址" />
        <el-table-column label="坐标" width="180">
          <template #default="scope">
            {{ formatCoords(scope.row.x, scope.row.y) }}
          </template>
        </el-table-column>
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
      :title="editingDepot ? '编辑仓库' : '添加仓库'"
      width="500px"
    >
      <el-form :model="depotForm" label-width="80px">
        <el-form-item label="仓库名称">
          <el-input v-model="depotForm.name" placeholder="例如：上海总仓" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="depotForm.address" placeholder="输入地址自动获取坐标" />
        </el-form-item>
        <el-form-item label="经度 (X)">
          <el-input-number v-model="depotForm.x" :precision="6" :step="0.0001" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="纬度 (Y)">
          <el-input-number v-model="depotForm.y" :precision="6" :step="0.0001" controls-position="right" style="width: 100%" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            {{ editingDepot ? '更新' : '添加' }}
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

const depots = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const submitLoading = ref(false)
const editingDepot = ref(null)

const depotForm = ref({
  name: '',
  address: '',
  x: null,
  y: null
})

const formatCoords = (x, y) => {
  if (x === null || y === null) return '-'
  return `${x.toFixed(4)}, ${y.toFixed(4)}`
}

const fetchDepots = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/depots/')
    depots.value = response.data
  } catch (error) {
    console.error('获取仓库列表失败:', error)
    ElMessage.error('获取仓库列表失败')
  } finally {
    loading.value = false
  }
}

const handleEdit = (depot) => {
  editingDepot.value = depot
  depotForm.value = {
    name: depot.name,
    address: depot.address,
    x: depot.x,
    y: depot.y
  }
  showAddDialog.value = true
}

const handleDelete = async (depot) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除仓库 "${depot.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`/api/depots/${depot.id}`)
    ElMessage.success('删除成功')
    fetchDepots()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除仓库失败:', error)
      ElMessage.error('删除仓库失败')
    }
  }
}

const handleSubmit = async () => {
  if (!depotForm.value.name || !depotForm.value.address) {
    ElMessage.warning('请输入名称和地址')
    return
  }
  
  submitLoading.value = true
  try {
    const payload = {
      name: depotForm.value.name,
      address: depotForm.value.address
    }
    // Only add coords if manually specified
    if (depotForm.value.x !== null && depotForm.value.y !== null) {
      payload.x = depotForm.value.x
      payload.y = depotForm.value.y
    }

    if (editingDepot.value) {
      await axios.put(`/api/depots/${editingDepot.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/api/depots/', payload)
      ElMessage.success('添加成功')
    }
    
    showAddDialog.value = false
    fetchDepots()
    
    if (!editingDepot.value) {
        depotForm.value = { name: '', address: '', x: null, y: null }
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败，请检查网络或地址有效性。')
  } finally {
    submitLoading.value = false
    editingDepot.value = null
  }
}

onMounted(() => {
  fetchDepots()
})
</script>

<style scoped>
/* .depots-container padding handled by Tailwind */

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
