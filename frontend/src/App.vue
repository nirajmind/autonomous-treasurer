<script setup>
import { ref, onMounted } from 'vue'
import LoginView from './components/LoginView.vue'
import DashboardView from './components/DashboardView.vue' // Ensure this matches your dashboard filename

const isAuthenticated = ref(false)

const checkAuth = () => {
  const token = localStorage.getItem('treasurer_token')
  isAuthenticated.value = !!token
}

const logout = () => {
  localStorage.removeItem('treasurer_token')
  isAuthenticated.value = false
}

onMounted(() => {
  checkAuth()
})
</script>

<template>
  <div>
    <div v-if="isAuthenticated">
      <DashboardView @logout="logout" />
    </div>

    <LoginView v-else @login-success="checkAuth" />
  </div>
</template>