<script setup>
import { ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['login-success'])

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)

    const res = await axios.post('https://smarttreasurer.duckdns.org/token', formData)
    
    // Save Token & Notify Parent
    localStorage.setItem('treasurer_token', res.data.access_token)
    emit('login-success')
    
  } catch (e) {
    error.value = "Access Denied: Invalid Credentials"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-900 flex items-center justify-center p-4">
    <div class="bg-slate-800 p-8 rounded-lg shadow-2xl border border-slate-700 w-full max-w-md">
      
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-emerald-400 mb-2">Autonomous Treasurer</h1>
        <p class="text-slate-400 text-sm">Authorized Personnel Only</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label class="block text-slate-300 text-sm font-bold mb-2">Username</label>
          <input v-model="username" type="text" class="w-full bg-slate-900 border border-slate-600 rounded p-3 text-white focus:border-emerald-500 focus:outline-none transition" placeholder="admin" required />
        </div>

        <div>
          <label class="block text-slate-300 text-sm font-bold mb-2">Password</label>
          <input v-model="password" type="password" class="w-full bg-slate-900 border border-slate-600 rounded p-3 text-white focus:border-emerald-500 focus:outline-none transition" placeholder="••••••••" required />
        </div>

        <div v-if="error" class="bg-red-500/10 border border-red-500 text-red-400 p-3 rounded text-sm text-center">
          {{ error }}
        </div>

        <button type="submit" :disabled="loading" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded transition flex justify-center items-center">
          <span v-if="loading" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></span>
          {{ loading ? 'Authenticating...' : 'Secure Login' }}
        </button>
      </form>
      
      <div class="mt-6 text-center">
        <p class="text-xs text-slate-600">System ID: TREASURER-AI-9000</p>
      </div>
    </div>
  </div>
</template>