<template>
  <div class="customers-container">
    <h1>客户管理</h1>
    
    <!-- 添加/编辑客户表单 -->
    <div class="form-section">
      <h2>{{ isEditing ? '编辑客户' : '添加新客户' }}</h2>
      <form @submit.prevent="handleSubmit">
        <div>
          <label for="name">姓名:</label>
          <input type="text" id="name" v-model="form.name" required />
        </div>
        <div>
          <label for="address">地址:</label>
          <input type="text" id="address" v-model="form.address" required />
        </div>
        <div>
          <label for="x">X 坐标:</label>
          <input type="number" step="0.0001" id="x" v-model.number="form.x" required />
        </div>
        <div>
          <label for="y">Y 坐标:</label>
          <input type="number" step="0.0001" id="y" v-model.number="form.y" required />
        </div>
        <button type="submit">{{ isEditing ? '更新' : '添加' }}</button>
        <button type="button" v-if="isEditing" @click="resetForm">取消</button>
      </form>
    </div>

    <!-- 客户列表 -->
    <div class="list-section">
      <h2>客户列表</h2>
      <table v-if="customers.length > 0">
        <thead>
          <tr>
            <th>ID</th>
            <th>姓名</th>
            <th>地址</th>
            <th>X 坐标</th>
            <th>Y 坐标</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="customer in customers" :key="customer.id">
            <td>{{ customer.id }}</td>
            <td>{{ customer.name }}</td>
            <td>{{ customer.address }}</td>
            <td>{{ customer.x }}</td>
            <td>{{ customer.y }}</td>
            <td>
              <button @click="editCustomer(customer)">编辑</button>
              <button @click="deleteCustomer(customer.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else>暂无客户信息。</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Customers',
  data() {
    return {
      customers: [],
      form: {
        name: '',
        address: '',
        x: 0,
        y: 0,
      },
      isEditing: false,
      editingId: null,
    };
  },
  async mounted() {
    await this.fetchCustomers();
  },
  methods: {
    async fetchCustomers() {
      try {
        const response = await axios.get('/api/customers/');
        this.customers = response.data;
      } catch (error) {
        console.error('获取客户列表失败:', error);
        alert('获取客户列表失败，请检查网络或登录状态。');
      }
    },
    async handleSubmit() {
      try {
        if (this.isEditing) {
          await axios.put(`/api/customers/${this.editingId}`, this.form);
          alert('客户信息已更新！');
        } else {
          await axios.post('/api/customers/', this.form);
          alert('新客户已添加！');
        }
        this.resetForm();
        await this.fetchCustomers();
      } catch (error) {
        console.error('提交客户信息失败:', error);
        alert('操作失败，请重试。');
      }
    },
    editCustomer(customer) {
      this.isEditing = true;
      this.editingId = customer.id;
      this.form = { ...customer };
    },
    async deleteCustomer(id) {
      if (confirm('确定要删除此客户吗？')) {
        try {
          await axios.delete(`/api/customers/${id}`);
          alert('客户已删除！');
          await this.fetchCustomers();
        } catch (error) {
          console.error('删除客户失败:', error);
          alert('删除失败，请重试。');
        }
      }
    },
    resetForm() {
      this.form = { name: '', address: '', x: 0, y: 0 };
      this.isEditing = false;
      this.editingId = null;
    },
  },
};
</script>

<style scoped>
.customers-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}
.form-section, .list-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}
form div {
  margin-bottom: 10px;
}
label {
  display: block;
  margin-bottom: 5px;
}
input[type="text"],
input[type="number"] {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
}
button {
  padding: 10px 15px;
  margin-right: 10px;
  cursor: pointer;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  padding: 10px;
  border: 1px solid #ddd;
  text-align: left;
}
th {
  background-color: #f2f2f2;
}
</style>