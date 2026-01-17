<template>
  <el-dialog
    v-model="visible"
    title="Terminal Console"
    width="800px"
    :before-close="handleClose"
    class="terminal-dialog"
    destroy-on-close
  >
    <div class="terminal-window" ref="terminalRef">
      <div v-if="logs.length === 0" class="empty-logs">
        No logs available.
      </div>
      <div v-for="(log, index) in logs" :key="index" class="log-line">
        {{ log }}
      </div>
      <div v-if="isRunning" class="loading-indicator">
        <span class="cursor">_</span>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'

const props = defineProps({
  visible: Boolean,
  taskId: String
})

const emit = defineEmits(['update:visible'])

const visible = ref(props.visible)
const logs = ref([])
const isRunning = ref(false)
const terminalRef = ref(null)
let pollingInterval = null

watch(() => props.visible, (val) => {
  visible.value = val
  if (val && props.taskId) {
    startPolling()
  } else {
    stopPolling()
  }
})

watch(() => props.taskId, (val) => {
  if (visible.value && val) {
    logs.value = []
    startPolling()
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const fetchLogs = async () => {
  if (!props.taskId) return
  try {
    const res = await axios.get(`/api/v1/tasks/${props.taskId}`)
    const task = res.data
    logs.value = task.logs || []
    isRunning.value = ['pending', 'processing'].includes(task.status)
    
    // Auto scroll to bottom
    nextTick(() => {
      if (terminalRef.value) {
        terminalRef.value.scrollTop = terminalRef.value.scrollHeight
      }
    })
    
    if (['completed', 'failed'].includes(task.status)) {
      stopPolling()
    }
  } catch (e) {
    console.error("Failed to fetch task logs", e)
  }
}

const startPolling = () => {
  stopPolling()
  fetchLogs() // Immediate
  pollingInterval = setInterval(fetchLogs, 1000)
}

const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.terminal-window {
  background-color: #1e1e1e;
  color: #00ff00;
  font-family: 'Courier New', Courier, monospace;
  padding: 16px;
  height: 400px;
  overflow-y: auto;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.4;
}

.log-line {
  word-break: break-all;
  white-space: pre-wrap;
  margin-bottom: 4px;
}

.empty-logs {
  color: #666;
  font-style: italic;
}

.cursor {
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>