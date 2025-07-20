<template>
  <el-card class="box-card">
    <template #header>
      <div class="card-header">
        <span>订单管理</span>
        <el-button class="button" type="primary" @click="handleCreate">新建订单</el-button>
      </div>
    </template>
    <el-table :data="orders" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="订单ID" width="100" />
      <el-table-column prop="customer.name" label="客户名称" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="scope">
          <el-tag :type="getStatusTag(scope.row.status)">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="demand" label="总需求 (重量)" width="150" />
      <el-table-column prop="created_at" label="创建时间">
        <template #default="scope">
          {{ new Date(scope.row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="scope">
          <el-button size="small" type="danger" @click="handleDelete(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <!-- 新建订单对话框 -->
  <el-dialog v-model="dialogVisible" title="新建订单" width="600px" @close="resetForm">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
      <el-form-item label="选择客户" prop="customer_id">
        <el-select v-model="form.customer_id" placeholder="请选择客户" filterable style="width: 100%">
          <el-option v-for="customer in customers" :key="customer.id" :label="customer.name" :value="customer.id" />
        </el-select>
      </el-form-item>
      <el-divider />
      <h4>订单商品</h4>
      <div v-for="(item, index) in form.items" :key="index" class="item-row">
        <el-form-item :prop="'items.' + index + '.product_id'" :rules="rules.product_id" label-width="0">
          <el-select v-model="item.product_id" placeholder="选择商品" filterable style="width: 200px; margin-right: 10px;">
            <el-option v-for="product in products" :key="product.id" :label="`${product.name} (${product.weight}kg)`" :value="product.id" />
          </el-select>
        </el-form-item>
        <el-form-item :prop="'items.' + index + '.quantity'" :rules="rules.quantity" label-width="0">
          <el-input-number v-model="item.quantity" :min="1" placeholder="数量" style="margin-right: 10px;" />
        </el-form-item>
        <el-button type="danger" :icon="Delete" circle @click="removeItem(index)" />
      </div>
      <el-button @click="addItem" style="margin-top: 10px;">添加商品</el-button>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">创建</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete } from '@element-plus/icons-vue';
import { useAuthStore } from '../store';

const orders = ref([]);
const customers = ref([]);
const products = ref([]);
const loading = ref(true);
const dialogVisible = ref(false);
const formRef = ref(null);

const authStore = useAuthStore();

const form = reactive({
  customer_id: null,
  items: [{ product_id: null, quantity: 1 }],
});

const rules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  product_id: [{ required: true, message: '请选择商品', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
};

const apiRequest = async (url, options) => {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authStore.token}`,
      ...options.headers,
    },
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || '操作失败');
  }
  // For DELETE requests, there might not be a JSON body
  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return null;
  }
  return response.json();
};

const fetchOrders = async () => {
  loading.value = true;
  try {
    orders.value = await apiRequest('/api/orders/', { method: 'GET' });
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loading.value = false;
  }
};

const fetchInitialData = async () => {
  try {
    [customers.value, products.value] = await Promise.all([
      apiRequest('/api/customers/', { method: 'GET' }),
      apiRequest('/api/products/', { method: 'GET' }),
    ]);
  } catch (error) {
    ElMessage.error('获取客户或商品列表失败');
  }
};

onMounted(() => {
  fetchOrders();
  fetchInitialData();
});

const resetForm = () => {
  form.customer_id = null;
  form.items = [{ product_id: null, quantity: 1 }];
};

const handleCreate = () => {
  resetForm();
  dialogVisible.value = true;
};

const addItem = () => {
  form.items.push({ product_id: null, quantity: 1 });
};

const removeItem = (index) => {
  if (form.items.length > 1) {
    form.items.splice(index, 1);
  }
};

const submitForm = () => {
  formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await apiRequest('/api/orders/', {
          method: 'POST',
          body: JSON.stringify(form),
        });
        ElMessage.success('订单创建成功');
        dialogVisible.value = false;
        fetchOrders();
      } catch (error) {
        ElMessage.error(error.message);
      }
    }
  });
};

const handleDelete = (id) => {
  ElMessageBox.confirm('此操作将永久删除该订单, 是否继续?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await apiRequest(`/api/orders/${id}`, { method: 'DELETE' });
      ElMessage.success('删除成功');
      fetchOrders();
    } catch (error) {
      ElMessage.error(error.message);
    }
  });
};

const getStatusTag = (status) => {
  switch (status) {
    case 'PENDING': return 'warning';
    case 'ASSIGNED': return 'primary';
    case 'IN_PROGRESS': return 'info';
    case 'COMPLETED': return 'success';
    case 'CANCELED': return 'danger';
    default: return 'info';
  }
};
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.item-row {
  display: flex;
  align-items: center;
  margin-bottom: 18px; /* Corresponds to el-form-item margin */
}
</style>