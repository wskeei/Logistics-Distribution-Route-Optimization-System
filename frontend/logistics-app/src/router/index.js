import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '../views/Dashboard.vue';
import RoutePlanning from '../views/RoutePlanning.vue';
import Login from '../views/Login.vue';
import Customers from '../views/Customers.vue';
import Tasks from '../views/Tasks.vue';
import Products from '../views/Products.vue';
import Orders from '../views/Orders.vue';
import Dispatcher from '../views/Dispatcher.vue';
import { useAuthStore } from '../store';

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
  },
  {
    path: '/planning',
    name: 'RoutePlanning',
    component: RoutePlanning,
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/customers',
    name: 'Customers',
    component: Customers,
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks,
    meta: { requiresAuth: true },
  },
  {
    path: '/products',
    name: 'Products',
    component: Products,
    meta: { requiresAuth: true },
  },
  {
    path: '/orders',
    name: 'Orders',
    component: Orders,
    meta: { requiresAuth: true },
  },
  {
    path: '/dispatcher',
    name: 'Dispatcher',
    component: Dispatcher,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// This is the most critical part. We attach the guard here.
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  const isLoggedIn = authStore.isAuthenticated;

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);

  if (requiresAuth && !isLoggedIn) {
    next({ name: 'Login' });
  } else {
    next();
  }
});

export default router;