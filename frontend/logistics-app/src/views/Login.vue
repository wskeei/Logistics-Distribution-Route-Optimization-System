<template>
  <div class="login-container">
    <div class="login-box">
      <h2>登录</h2>
      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <label for="username">用户名</label>
          <input type="text" id="username" v-model="username" required>
        </div>
        <div class="input-group">
          <label for="password">密码</label>
          <input type="password" id="password" v-model="password" required>
        </div>
        <p v-if="error" class="error-message">{{ error }}</p>
        <button type="submit">登录</button>
      </form>
      <p class="register-prompt">
        还没有账户? <a href="#" @click.prevent="isRegistering = true">立即注册</a>
      </p>
    </div>

    <!-- Registration Modal -->
    <div v-if="isRegistering" class="modal-overlay" @click.self="isRegistering = false">
      <div class="modal-box">
        <h2>注册新用户</h2>
        <form @submit.prevent="handleRegister">
          <div class="input-group">
            <label for="reg-username">用户名</label>
            <input type="text" id="reg-username" v-model="regUsername" required>
          </div>
          <div class="input-group">
            <label for="reg-password">密码</label>
            <input type="password" id="reg-password" v-model="regPassword" required>
          </div>
          <p v-if="regError" class="error-message">{{ regError }}</p>
          <button type="submit">注册</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store';

const router = useRouter();
const authStore = useAuthStore();

// Login state
const username = ref('');
const password = ref('');
const error = ref('');

// Registration state
const isRegistering = ref(false);
const regUsername = ref('');
const regPassword = ref('');
const regError = ref('');

const handleLogin = async () => {
  error.value = '';
  try {
    await authStore.login(username.value, password.value);
    router.push('/');
  } catch (err) {
    error.value = '登录失败，请检查用户名和密码。';
  }
};

const handleRegister = async () => {
  regError.value = '';
  if (regPassword.value.length < 4) {
      regError.value = '密码长度不能少于4位。';
      return;
  }
  try {
    await authStore.register(regUsername.value, regPassword.value);
    isRegistering.value = false;
    // Auto-fill login form after successful registration
    username.value = regUsername.value;
    password.value = regPassword.value;
    alert('注册成功！请使用新账户登录。');
  } catch (err) {
    regError.value = '注册失败，用户名可能已被占用。';
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}
.login-box {
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  width: 360px;
  text-align: center;
}
h2 {
  margin-bottom: 20px;
}
.input-group {
  margin-bottom: 15px;
  text-align: left;
}
label {
  display: block;
  margin-bottom: 5px;
}
input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
button {
  width: 100%;
  padding: 10px;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}
.error-message {
  color: red;
  margin-bottom: 15px;
}
.register-prompt {
  margin-top: 20px;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal-box {
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  width: 360px;
  text-align: center;
}
</style>