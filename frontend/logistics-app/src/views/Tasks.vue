<template>
  <div class="tasks-container">
    <h1>任务管理</h1>

    <!-- 创建新任务表单 -->
    <div class="form-section">
      <h2>创建新任务</h2>
      <form @submit.prevent="createTask">
        <div>
          <label for="depot">选择仓库:</label>
          <select id="depot" v-model="newTask.depot_id" required>
            <option disabled value="">请选择仓库</option>
            <option v-for="depot in depots" :key="depot.id" :value="depot.id">
              {{ depot.name }} ({{ depot.address }})
            </option>
          </select>
        </div>
        <div>
          <label for="vehicle">选择车辆 (可选):</label>
          <select id="vehicle" v-model="newTask.vehicle_id">
            <option :value="null">不指定车辆</option>
            <option v-for="vehicle in vehicles" :key="vehicle.id" :value="vehicle.id">
              {{ vehicle.name }} (容量: {{ vehicle.capacity }})
            </option>
          </select>
        </div>
        <div>
          <label>选择客户:</label>
          <div class="customer-selection">
            <label v-for="customer in customers" :key="customer.id">
              <input type="checkbox" :value="customer.id" v-model="selectedCustomerIds" />
              {{ customer.name }} ({{ customer.address }})
            </label>
          </div>
        </div>
        <button type="submit" :disabled="selectedCustomerIds.length === 0 || !newTask.depot_id">
          创建并优化任务
        </button>
      </form>
    </div>

    <!-- 任务列表 -->
    <div class="list-section">
      <h2>任务列表</h2>
      <table v-if="tasks.length > 0">
        <thead>
          <tr>
            <th>ID</th>
            <th>创建时间</th>
            <th>状态</th>
            <th>仓库</th>
            <th>车辆</th>
            <th>总距离</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td>{{ task.id }}</td>
            <td>{{ new Date(task.created_at).toLocaleString() }}</td>
            <td>{{ task.status }}</td>
            <td>{{ task.depot?.name || 'N/A' }}</td>
            <td>{{ task.vehicle?.name || '未分配' }}</td>
            <td>{{ task.total_distance ? task.total_distance.toFixed(2) : 'N/A' }}</td>
            <td>
              <button @click="viewTaskDetails(task.id)">查看详情</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else>暂无任务。</p>
    </div>

    <!-- 任务详情弹窗 -->
    <div v-if="selectedTask" class="modal-overlay" @click="selectedTask = null">
      <div class="modal-content" @click.stop>
        <h3>任务详情 - ID: {{ selectedTask.id }}</h3>
        <p><strong>状态:</strong> {{ selectedTask.status }}</p>
        <p><strong>仓库:</strong> {{ selectedTask.depot?.name }} ({{ selectedTask.depot?.address }})</p>
        <p><strong>车辆:</strong> {{ selectedTask.vehicle?.name || '未分配' }}</p>
        <p><strong>总距离:</strong> {{ selectedTask.total_distance ? selectedTask.total_distance.toFixed(2) : 'N/A' }}</p>
        <h4>配送路径:</h4>
        <ol>
          <li>{{ selectedTask.depot?.name }} (起点)</li>
          <li v-for="stop in selectedTask.stops" :key="stop.id">
            {{ stop.customer.name }} ({{ stop.customer.address }})
          </li>
          <li>{{ selectedTask.depot?.name }} (终点)</li>
        </ol>
        <button @click="selectedTask = null">关闭</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Tasks',
  data() {
    return {
      depots: [],
      vehicles: [],
      customers: [],
      tasks: [],
      newTask: {
        depot_id: '',
        vehicle_id: null,
      },
      selectedCustomerIds: [],
      selectedTask: null,
    };
  },
  async mounted() {
    await this.fetchInitialData();
    await this.fetchTasks();
  },
  methods: {
    async fetchInitialData() {
      try {
        const [depotsRes, vehiclesRes, customersRes] = await Promise.all([
          axios.get('/api/depots/'),
          axios.get('/api/vehicles/'),
          axios.get('/api/customers/'),
        ]);
        this.depots = depotsRes.data;
        this.vehicles = vehiclesRes.data;
        this.customers = customersRes.data;
      } catch (error) {
        console.error('获取初始数据失败:', error);
        alert('获取初始数据失败，请检查网络或登录状态。');
      }
    },
    async fetchTasks() {
      try {
        const response = await axios.get('/api/tasks/');
        this.tasks = response.data;
      } catch (error) {
        console.error('获取任务列表失败:', error);
      }
    },
    async createTask() {
      if (!this.newTask.depot_id || this.selectedCustomerIds.length === 0) {
        alert('请选择仓库和至少一个客户。');
        return;
      }

      try {
        const payload = {
          depot_id: this.newTask.depot_id,
          vehicle_id: this.newTask.vehicle_id,
          customer_ids: this.selectedCustomerIds,
        };
        const response = await axios.post('/api/tasks/optimize', payload);
        alert(`任务创建并优化成功！总距离: ${response.data.total_distance?.toFixed(2) || 'N/A'}`);
        this.resetForm();
        await this.fetchTasks();
      } catch (error) {
        console.error('创建任务失败:', error);
        alert('创建任务失败，请重试。');
      }
    },
    async viewTaskDetails(taskId) {
      try {
        const response = await axios.get(`/api/tasks/${taskId}`);
        this.selectedTask = response.data;
      } catch (error) {
        console.error('获取任务详情失败:', error);
        alert('获取任务详情失败。');
      }
    },
    resetForm() {
      this.newTask = { depot_id: '', vehicle_id: null };
      this.selectedCustomerIds = [];
    },
  },
};
</script>

<style scoped>
.tasks-container {
  max-width: 1000px;
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
  margin-bottom: 15px;
}
label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}
select, button {
  padding: 8px;
  margin-top: 5px;
}
.customer-selection {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #ccc;
  padding: 10px;
  border-radius: 4px;
}
.customer-selection label {
  display: block;
  margin-bottom: 5px;
  font-weight: normal;
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
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}
</style>