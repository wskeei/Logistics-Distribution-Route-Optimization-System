<template>
  <el-card class="box-card">
    <template #header>
      <div class="card-header">
        <span>货物管理</span>
        <el-button class="button" type="primary" @click="handleCreate">新建货物</el-button>
      </div>
    </template>
    <el-table :data="products" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="货物ID" width="100" />
      <el-table-column prop="name" label="货物名称" />
      <el-table-column prop="weight" label="重量 (kg)" />
      <el-table-column label="操作" width="150">
        <template #default="scope">
          <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <!-- 新建/编辑货物对话框 -->
  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑货物' : '新建货物'" width="500px" @close="resetForm">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
      <el-form-item label="货物名称" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="重量 (kg)" prop="weight">
        <el-input-number v-model="form.weight" :precision="2" :step="0.1" :min="0" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAuthStore } from '../store';

const products = ref([]);
const loading = ref(true);
const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref(null);
const currentProductId = ref(null);

const authStore = useAuthStore();

const form = reactive({
  name: '',
  weight: 0,
});

const rules = {
  name: [{ required: true, message: '请输入货物名称', trigger: 'blur' }],
  weight: [{ required: true, message: '请输入重量', trigger: 'blur' }],
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
  return response.json();
};

const fetchProducts = async () => {
  loading.value = true;
  try {
    products.value = await apiRequest('/api/products/', { method: 'GET' });
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchProducts);

const resetForm = () => {
  form.name = '';
  form.weight = 0;
  currentProductId.value = null;
  isEdit.value = false;
};

const handleCreate = () => {
  resetForm();
  dialogVisible.value = true;
};

const handleEdit = (product) => {
  isEdit.value = true;
  currentProductId.value = product.id;
  form.name = product.name;
  form.weight = product.weight;
  dialogVisible.value = true;
};

const submitForm = () => {
  formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (isEdit.value) {
          await apiRequest(`/api/products/${currentProductId.value}`, {
            method: 'PUT',
            body: JSON.stringify(form),
          });
          ElMessage.success('更新成功');
        } else {
          await apiRequest('/api/products/', {
            method: 'POST',
            body: JSON.stringify(form),
          });
          ElMessage.success('创建成功');
        }
        dialogVisible.value = false;
        fetchProducts();
      } catch (error) {
        ElMessage.error(error.message);
      }
    }
  });
};

const handleDelete = (id) => {
  ElMessageBox.confirm('此操作将永久删除该货物, 是否继续?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await apiRequest(`/api/products/${id}`, { method: 'DELETE' });
      ElMessage.success('删除成功');
      fetchProducts();
    } catch (error) {
      ElMessage.error(error.message);
    }
  });
};
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>