<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// Define the logout event
const emit = defineEmits(['logout'])

// --- STATE VARIABLES ---
const runwayMonths = ref(0)
const mneeBalance = ref(0)
const burnRate = ref(5000)
const isOnline = ref(false)
const liquidityLogs = ref([]) // <--- This will now be populated

// --- CFO CONTROL STATE ---
const approvalLimit = ref(50)
const token = localStorage.getItem('treasurer_token')

// --- API ACTIONS ---

// 1. Fetch Main Stats (Balance & Runway)
const fetchFinancialStatus = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/dashboard', {
        headers: { Authorization: `Bearer ${token}` }
    })
    
    const data = response.data
    if (data.status === 'Online' || data.treasury_balance !== undefined) {
      mneeBalance.value = data.treasury_balance
      runwayMonths.value = data.runway_months
      burnRate.value = data.monthly_burn
      isOnline.value = true
    }
  } catch (error) {
    console.error("Stats Failed:", error)
    isOnline.value = false
    if (error.response && error.response.status === 401) emit('logout')
  }
}

// 2. Fetch Logs (The Missing Part!)
const fetchLogs = async () => {
  try {
      const response = await axios.get('http://localhost:8000/api/dashboard/logs', {
          headers: { Authorization: `Bearer ${token}` }
      })
      // Only update if we actually got data back
      if (Array.isArray(response.data)) {
          liquidityLogs.value = response.data
      }
  } catch (e) {
      console.error("Logs Failed:", e)
  }
}

// 3. Fetch Policy Limit
const fetchLimit = async () => {
    try {
        const res = await axios.get('http://localhost:8000/api/settings/limit', {
            headers: { Authorization: `Bearer ${token}` }
        })
        approvalLimit.value = res.data.limit
    } catch (e) { console.error("Limit Failed", e) }
}

// 4. Update Policy
const updateLimit = async () => {
    try {
        await axios.post(
            'http://localhost:8000/api/settings/limit', 
            { new_limit: approvalLimit.value }, 
            { headers: { Authorization: `Bearer ${token}` } }
        )
        alert("✅ Policy Updated Successfully!")
    } catch (e) {
        if (e.response && e.response.status === 401) {
            alert("❌ Session Expired.")
            emit('logout')
        } else {
            alert("❌ Failed: " + (e.response?.data?.detail || "Error"))
        }
    }
}

// Utility
const formatTime = (ts) => {
  if (!ts) return ''
  return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// Lifecycle
onMounted(() => {
  if (!token) {
      emit('logout')
      return
  }
  // Initial Load
  fetchFinancialStatus()
  fetchLogs() // <--- Now calling logs!
  fetchLimit()

  // Poll every 2 seconds for live updates
  setInterval(() => {
      fetchFinancialStatus()
      fetchLogs()
  }, 2000)
})
</script>

<template>
  <div class="min-h-screen bg-slate-900 text-white p-8 font-mono">
    
    <header class="mb-8 border-b border-slate-700 pb-4 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-emerald-400">The Autonomous Treasurer</h1>
        <p class="text-slate-400">AI-Driven Financial Runway Management</p>
      </div>
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
            <span class="h-3 w-3 rounded-full" :class="isOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'"></span>
            <span class="text-xs uppercase">{{ isOnline ? 'System Online' : 'Offline' }}</span>
        </div>
        <button @click="$emit('logout')" class="bg-red-500/20 hover:bg-red-500/40 text-red-400 text-xs px-3 py-1 rounded border border-red-500 transition">
            LOGOUT
        </button>
      </div>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      
      <div class="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg">
        <h2 class="text-xl mb-4 text-slate-300 border-b border-slate-700 pb-2">Runway Health</h2>
        <div class="text-center py-8">
          <div class="text-6xl font-bold transition-all duration-500" 
               :class="runwayMonths > 1 ? 'text-emerald-400' : 'text-red-500'">
            {{ runwayMonths }}
          </div>
          <div class="text-sm text-slate-500 uppercase tracking-widest mt-2">Months Left</div>
        </div>
        <div class="space-y-4 mt-4 bg-slate-900 p-4 rounded">
          <div class="flex justify-between border-b border-slate-800 pb-2">
            <span class="text-slate-400">Treasury Balance:</span>
            <span class="font-bold text-emerald-300">{{ mneeBalance }} MNEE</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">Monthly Burn (Est):</span>
            <span class="font-bold text-red-400">-{{ burnRate }} MNEE</span>
          </div>
        </div>
      </div>

      <div class="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg flex flex-col justify-center">
        <h2 class="text-xl mb-4 text-slate-300 border-b border-slate-700 pb-2">⚙️ CFO Policy Controls</h2>
        
        <div class="space-y-6">
            <div class="bg-slate-900 p-4 rounded border border-slate-600">
                <label class="block text-slate-400 text-sm mb-3">Auto-Approval Limit ($)</label>
                <div class="flex items-center gap-4">
                    <input type="number" v-model="approvalLimit" class="bg-slate-800 border border-slate-500 p-3 rounded text-white w-28 text-center font-bold text-xl focus:border-emerald-500 focus:outline-none" />
                    <button @click="updateLimit" class="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white p-3 rounded font-bold transition shadow-lg">
                        Update Policy
                    </button>
                </div>
            </div>
            
            <div class="text-xs text-slate-500">
                <p class="mb-2">ℹ️ <strong>Policy Logic:</strong></p>
                <ul class="list-disc pl-4 space-y-1">
                    <li>Transactions <strong>below</strong> limit: Processed on-chain immediately.</li>
                    <li>Transactions <strong>above</strong> limit: Paused for manual review.</li>
                    <li>Current Admin: <span class="text-emerald-400">Authenticated</span></li>
                </ul>
            </div>
        </div>
      </div>

      <div class="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg md:col-span-3">
        <h2 class="text-xl mb-4 text-slate-300 border-b border-slate-700 pb-2">
          Live Liquidity Ledger (Redis Stream)
        </h2>
        
        <div class="space-y-2 h-64 overflow-y-auto pr-2">
          <div v-if="liquidityLogs.length === 0" class="text-slate-500 text-center py-10">
            Waiting for blockchain activity...
          </div>

          <div v-for="(log, index) in liquidityLogs" :key="index" 
               class="p-3 rounded flex justify-between items-center border-l-4 bg-slate-900 transition-all hover:bg-slate-800"
               :class="{
                 'border-emerald-500': log.status === 'CONFIRMED' || log.status === 'TX_PENDING',
                 'border-red-500': log.status === 'FAILED_NO_LIQUIDITY',
                 'border-blue-500': log.status === 'CHECKED',
                 'border-orange-500': log.status.includes('SENT')
               }">
            
            <div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-slate-500 font-bold">{{ formatTime(log.timestamp) }}</span>
                <span class="font-bold text-sm">{{ log.event }}</span>
              </div>
              <div class="text-xs mt-1 text-slate-400">
                Status: <span :class="{
                  'text-red-400': log.status === 'FAILED_NO_LIQUIDITY',
                  'text-blue-400': log.status === 'CHECKED',
                  'text-orange-400': log.status.includes('SENT')
                }">{{ log.status }}</span>
              </div>
            </div>

            <div class="text-right">
              <div class="font-bold text-sm" :class="log.balance > 0 ? 'text-emerald-400' : 'text-slate-400'">
                Bal: {{ log.balance }} MNEE
              </div>
              <div v-if="log.required" class="text-xs text-red-400">
                Req: {{ log.required }} MNEE
              </div>
            </div>

          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>