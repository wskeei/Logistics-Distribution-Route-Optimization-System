<template>
  <div class="customers-container p-6 md:p-8">
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

      <el-table :data="customers" style="width: 100%" v-loading="loading" @row-click="handleRowClick" row-class-name="cursor-pointer">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="客户名称" />
        <el-table-column prop="address" label="地址" />
        <el-table-column label="坐标" width="200">
          <template #default="scope">
            {{ scope.row.x }}, {{ scope.row.y }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
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

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingCustomer ? '编辑客户' : '添加客户'"
      width="500px"
    >
      <el-form :model="customerForm" label-width="100px">
        <el-form-item label="客户名称">
          <el-input v-model="customerForm.name" autocomplete="off" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="customerForm.address" autocomplete="off" />
        </el-form-item>
        <el-form-item label="X 坐标">
          <el-input-number v-model="customerForm.x" :precision="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="Y 坐标">
          <el-input-number v-model="customerForm.y" :precision="2" :step="0.1" />
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

    <!-- Detail Dialog -->
    <el-dialog
      v-model="showDetailDialog"
      title="客户详情"
      width="700px"
    >
      <div v-if="currentCustomer">
        <el-descriptions title="基本信息" :column="2" border>
            <el-descriptions-item label="ID">{{ currentCustomer.id }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ currentCustomer.name }}</el-descriptions-item>
            <el-descriptions-item label="地址" :span="2">{{ currentCustomer.address }}</el-descriptions-item>
            <el-descriptions-item label="坐标">({{ currentCustomer.x }}, {{ currentCustomer.y }})</el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <h3>关联订单</h3>
        <el-table :data="customerOrders" style="width: 100%" height="250" empty-text="暂无订单数据">
            <el-table-column prop="id" label="订单ID" width="80" />
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column prop="demand" label="需求量" />
            <el-table-column prop="created_at" label="创建时间">
                <template #default="scope">
                    {{ new Date(scope.row.created_at).toLocaleString() }}
                </template>
            </el-table-column>
        </el-table>
      </div>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const customers = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const submitLoading = ref(false)
const editingCustomer = ref(null)

// Detail View State
const showDetailDialog = ref(false)
const currentCustomer = ref(null)
const allOrders = ref([])

const customerForm = ref({
  name: '',
  address: '',
  x: 0.0,
  y: 0.0
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

// Fetch orders to display in detail view
const fetchOrders = async () => {
    try {
        const res = await axios.get('/api/orders/?limit=1000'); // Fetch enough orders
        allOrders.value = res.data;
    } catch (e) {
        console.error("Failed to fetch orders", e);
    }
}

const handleRowClick = (row) => {
    currentCustomer.value = row;
    showDetailDialog.value = true;
    if (allOrders.value.length === 0) {
        fetchOrders(); // Lazy fetch if not loaded
    }
}

const customerOrders = computed(() => {
    if (!currentCustomer.value || !allOrders.value) return [];
    return allOrders.value.filter(o => o.customer.id === currentCustomer.value.id);
});

const handleAdd = () => {
  editingCustomer.value = null
  customerForm.value = {
    name: '',
    address: '',
    x: 0.0,
    y: 0.0
  }
  showAddDialog.value = true
}

const handleEdit = (customer) => {
  editingCustomer.value = customer
  customerForm.value = {
    name: customer.name,
    address: customer.address,
    x: customer.x,
    y: customer.y
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
  if (!customerForm.value.name) {
    ElMessage.warning('请输入客户名称')
    return
  }
  
  submitLoading.value = true
  try {
    if (editingCustomer.value) {
      await axios.put(`/api/customers/${editingCustomer.value.id}`, customerForm.value)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/api/customers/', customerForm.value)
      ElMessage.success('添加成功')
    }
    
    showAddDialog.value = false
    fetchCustomers()
    if (!editingCustomer.value) {
        customerForm.value = { name: '', address: '', x: 0.0, y: 0.0 }
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败')
  } finally {
    submitLoading.value = false
    editingCustomer.value = null
  }
}

onMounted(() => {
  fetchCustomers();
  fetchOrders(); // Pre-fetch orders or do it on click
})
</script>

<style scoped>
/* .customers-container padding handled by Tailwind */


.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>