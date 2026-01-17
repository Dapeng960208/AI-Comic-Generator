<template>
  <div v-if="tasks.length > 0" class="task-manager" :class="{ collapsed: isCollapsed }">
    <div class="task-header" @click="toggleCollapse">
      <span>Background Tasks ({{ runningCount }})</span>
      <el-icon><component :is="isCollapsed ? 'ArrowUp' : 'ArrowDown'" /></el-icon>
    </div>
    <div v-show="!isCollapsed" class="task-list">
      <div v-for="task in tasks" :key="task.id" class="task-item">
        <div class="task-info">
          <div class="task-name-group">
            <span class="task-name" :title="task.description">{{ task.name || getTaskTypeName(task.type) }}</span>
            <span class="task-desc" v-if="task.description">{{ task.description }}</span>
            <span class="task-error" v-if="task.status === 'failed' && task.message" :title="task.message">
              Failure Reason: {{ task.message }}
            </span>
          </div>
          <div class="status-group">
             <el-button link size="small" @click.stop="openTerminal(task.id)" title="View Logs">
                <el-icon><Monitor /></el-icon>
             </el-button>
             <span class="task-status" :class="task.status">{{ getTaskStatusText(task.status) }}</span>
          </div>
        </div>
        <el-progress :percentage="task.progress" :status="getTaskProgressStatus(task.status)" :stroke-width="6"></el-progress>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowUp, ArrowDown, Monitor } from '@element-plus/icons-vue'

const props = defineProps({
  tasks: {
    type: Array,
    required: true
  },
  isCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:isCollapsed', 'open-terminal'])

const runningCount = computed(() => {
  return props.tasks.filter(t => ['pending', 'processing'].includes(t.status)).length
})

const toggleCollapse = () => {
  emit('update:isCollapsed', !props.isCollapsed)
}

const openTerminal = (taskId) => {
    emit('open-terminal', taskId)
}

const getTaskTypeName = (type) => {
  const map = {
    'storyboard': 'Storyboard Generation',
    'image_generation': 'Full Image Generation',
    'character_generation': 'Character Drawing'
  }
  return map[type] || type
}

const getTaskStatusText = (status) => {
  const map = {
    'pending': 'Pending',
    'processing': 'Processing',
    'completed': 'Completed',
    'failed': 'Failed'
  }
  return map[status] || status
}

const getTaskProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return ''
}
</script>

<style scoped>
.task-manager {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 320px;
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 0;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    transition: all 0.3s ease;
    overflow: hidden;
}
.task-manager.collapsed {
    width: 200px;
}
.task-header {
    font-weight: bold;
    padding: 10px 15px;
    background: #2b2b2b;
    border-bottom: 1px solid #333;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    user-select: none;
}
.task-header:hover {
    background: #333;
}
.task-list {
    max-height: 300px;
    overflow-y: auto;
    padding: 10px;
}
.task-item {
    margin-bottom: 15px;
    font-size: 0.9em;
    padding-bottom: 10px;
    border-bottom: 1px solid #2a2a2a;
}
.task-item:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}
.task-info {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 6px;
}
.task-name-group {
    display: flex;
    flex-direction: column;
    max-width: 60%;
}
.status-group {
    display: flex;
    align-items: center;
    gap: 8px;
}
.task-name {
    font-weight: bold;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.task-desc {
    font-size: 0.8em;
    color: #888;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.task-error {
    font-size: 0.8em;
    color: #F56C6C;
    margin-top: 2px;
    word-break: break-all;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.task-status.pending { color: #909399; }
.task-status.processing { color: #409EFF; }
.task-status.completed { color: #67C23A; }
.task-status.failed { color: #F56C6C; }
</style>