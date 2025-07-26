<template>
  <div class="customers-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>客户管理</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加客户
          </el-button>
        </div>
      </template>

      <el-table :data="customers" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="客户名称" />
        <el-table-column prop="address" label="地址" />
        <el-table-column prop="y" label="纬度" width="100" />
        <el-table-column prop="x" label="经度" width="100" />
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

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingCustomer ? '编辑客户' : '添加客户'"
      width="500px"
    >
      <el-form :model="customerForm" label-width="80px">
        <el-form-item label="客户名称">
          <el-input v-model="customerForm.name" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="customerForm.address" />
        </el-form-item>
        <el-form-item label="纬度">
          <el-input-number v-model="customerForm.latitude" :precision="6" :step="0.0001" controls-position="right" />
        </el-form-item>
        <el-form-item label="经度">
          <el-input-number v-model="customerForm.longitude" :precision="6" :step="0.0001" controls-position="right" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            {{ editingCustomer ? '更新' : '添加' }}
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

const customers = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const submitLoading = ref(false)
const editingCustomer = ref(null)

const customerForm = ref({
  name: '',
  address: '',
  latitude: null,
  longitude: null
})

const fetchCustomers = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/customers/')
    customers.value = response.data
  } catch (error) {
    console.error('获取客户列表失败:', error)
    ElMessage.error('获取客户列表失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  editingCustomer.value = null
  customerForm.value = {
    name: '',
    address: '',
    latitude: null,
    longitude: null
  }
  showAddDialog.value = true
}

const handleEdit = (customer) => {
  editingCustomer.value = customer
  // 将后端的 x, y 映射到前端表单的 longitude, latitude
  customerForm.value = {
    name: customer.name,
    address: customer.address,
    latitude: customer.y,
    longitude: customer.x,
  }
  showAddDialog.value = true
}

const handleDelete = async (customer) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除客户 "${customer.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`/api/customers/${customer.id}`)
    ElMessage.success('删除成功')
    fetchCustomers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除客户失败:', error)
      ElMessage.error('删除客户失败')
    }
  }
}

const handleSubmit = async () => {
  submitLoading.value = true
  try {
    // 映射前端表单数据到后端需要的格式
    const payload = {
      name: customerForm.value.name,
      address: customerForm.value.address,
    };

    // Only include coordinates if they are provided
    if (customerForm.value.longitude !== null && customerForm.value.latitude !== null) {
      payload.x = customerForm.value.longitude;
      payload.y = customerForm.value.latitude;
    }

    if (editingCustomer.value) {
      await axios.put(`/api/customers/${editingCustomer.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/api/customers/', payload)
      ElMessage.success('添加成功')
    }
    
    showAddDialog.value = false
    fetchCustomers()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败，请检查输入数据。')
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  fetchCustomers()
})
</script>

<style scoped>
.customers-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>