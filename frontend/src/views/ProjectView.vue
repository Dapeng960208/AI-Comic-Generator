<template>
  <div class="project-view" v-loading="loading" element-loading-text="Processing..." element-loading-background="rgba(0, 0, 0, 0.8)">
    <ProjectHeader 
      :title="project.title" 
      @export="openExportDialog" 
    />

    <TaskManager 
      :tasks="activeTasks" 
      v-model:isCollapsed="isTaskManagerCollapsed" 
      @open-terminal="openTerminal"
    />

    <el-tabs v-model="activeTab" class="workflow-tabs">
      <el-tab-pane label="1. Story & Config" name="story">
        <StoryTab 
          :project="project" 
          :project-id="projectId" 
          :is-task-running="isTaskRunning"
          @refresh-project="fetchProject"
          @task-started="pollActiveTasks"
        />
      </el-tab-pane>

      <el-tab-pane label="2. Character Studio" name="characters">
        <CharacterTab 
          :project="project" 
          :project-id="projectId" 
          :is-task-running="isTaskRunning"
          :image-version="imageVersion"
          @refresh-project="fetchProject"
          @task-started="pollActiveTasks"
          @open-merge-dialog="showMergeDialog = true"
          @open-history="openHistory"
        />
      </el-tab-pane>

      <el-tab-pane label="3. Storyboard Canvas" name="comic">
        <StoryboardTab 
          :project="project" 
          :project-id="projectId" 
          :is-task-running="isTaskRunning"
          :image-version="imageVersion"
          @refresh-project="fetchProject"
          @task-started="pollActiveTasks"
          @open-history="openHistory"
        />
      </el-tab-pane>
    </el-tabs>

    <MergeDialog 
      v-model:visible="showMergeDialog"
      :characters="project.characters"
      :project-id="projectId"
      @merged="fetchProject"
    />

    <ExportDialog 
      v-model:visible="showExportDialog"
      :project-id="projectId"
    />

    <HistoryDialog 
      v-model:visible="showHistoryDialog"
      :type="currentHistoryType"
      :entity-id="currentHistoryEntityId"
      :current-image-url="currentHistoryImageUrl"
      @image-selected="fetchProject"
    />

    <TerminalDialog
      v-model:visible="showTerminalDialog"
      :task-id="currentTerminalTaskId"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { ElNotification } from 'element-plus'

import ProjectHeader from './project/ProjectHeader.vue'
import StoryTab from './project/StoryTab.vue'
import CharacterTab from './project/CharacterTab.vue'
import StoryboardTab from './project/StoryboardTab.vue'
import TaskManager from './project/TaskManager.vue'
import HistoryDialog from './project/HistoryDialog.vue'
import MergeDialog from './project/MergeDialog.vue'
import ExportDialog from './project/ExportDialog.vue'
import TerminalDialog from './project/TerminalDialog.vue'

const route = useRoute()
const projectId = route.params.id

// Project State
const project = ref({
    title: '',
    theme: '',
    language: 'zh-CN',
    panel_count: undefined,
    aspect_ratio: '16:9',
    resolution: '2K',
    characters: [],
    storyboard_items: [],
    story_input: '',
    global_config: null
})
const loading = ref(false)
const activeTab = ref('story')
const imageVersion = ref(Date.now())

// Task State
const activeTasks = ref([])
const isTaskManagerCollapsed = ref(true)
const taskPollingInterval = ref(null)

// Dialog State
const showMergeDialog = ref(false)
const showExportDialog = ref(false)
const showHistoryDialog = ref(false)
const showTerminalDialog = ref(false)
const currentTerminalTaskId = ref('')

// History State
const currentHistoryType = ref('')
const currentHistoryEntityId = ref('')

const currentHistoryImageUrl = computed(() => {
    if (currentHistoryType.value === 'character') {
        const char = project.value.characters.find(c => c.id === currentHistoryEntityId.value)
        return char?.image_url
    } else {
        const item = project.value.storyboard_items.find(i => i.id === currentHistoryEntityId.value)
        return item?.image_url
    }
})

const isTaskRunning = computed(() => {
    return activeTasks.value.some(t => ['pending', 'processing'].includes(t.status))
})

// Fetch Data
const fetchProject = async () => {
    try {
        const res = await axios.get(`/api/v1/projects/${projectId}`)
        // Update fields individually to preserve references where possible, 
        // though replacing the whole object is cleaner if children watch correctly.
        // Our children watch deep or props change, so replacing is fine but might reset some local state if not careful.
        // Let's do a merge or simple assign.
        project.value = res.data
        // Ensure arrays are at least empty arrays
        if (!project.value.characters) project.value.characters = []
        if (!project.value.storyboard_items) project.value.storyboard_items = []
        // imageVersion.value = Date.now() // Disabled to prevent flickering. Backend uses unique filenames.
    } catch (error) {
        console.error('Fetch project error', error)
    } finally {
        loading.value = false
    }
}

// Task Polling
const pollActiveTasks = async () => {
    if (taskPollingInterval.value) clearInterval(taskPollingInterval.value)
    
    // Immediate check
    checkTasks()

    taskPollingInterval.value = setInterval(checkTasks, 2000)
}

const checkTasks = async () => {
    try {
        const res = await axios.get(`/api/v1/tasks/project/${projectId}`)
        activeTasks.value = res.data.slice(0, 5) // Top 5
        
        // Check if we need to refresh project data
        // If any task completed since last check (we can't easily track "since last check" without state, 
        // but we can check if any task is processing, or if we just had a completion)
        
        const anyProcessing = res.data.some(t => t.status === 'processing')
        if (anyProcessing) {
            // Optional: periodically refresh project to see partial updates? 
            // Or just wait for completion.
            // Original code refreshed on completion or processing.
            // Let's refresh only on completion events handled by the watcher below.
            
            // To support real-time image updates during batch generation:
            fetchProject()
        }
    } catch (e) {
        console.error("Polling error", e)
    }
}

// Watch tasks for completion
watch(activeTasks, (newTasks, oldTasks) => {
    if (oldTasks.length === 0) return
    
    const changed = newTasks.some(t => {
        const old = oldTasks.find(o => o.id === t.id)
        return t.status === 'completed' && old && old.status !== 'completed'
    })
    
    if (changed) {
        fetchProject()
        ElNotification({ title: 'Task Completed', message: 'Background tasks updated', type: 'success' })
    }
}, { deep: true })

// Actions
const openExportDialog = () => {
    if (!project.value.characters.length && !project.value.storyboard_items.some(i => i.image_url)) {
        ElNotification({ title: 'Warning', message: 'No exportable image content', type: 'warning' })
        return
    }
    showExportDialog.value = true
}

const openHistory = (type, id) => {
    currentHistoryType.value = type
    currentHistoryEntityId.value = id
    showHistoryDialog.value = true
}

const openTerminal = (taskId) => {
    currentTerminalTaskId.value = taskId
    showTerminalDialog.value = true
}

// Lifecycle
onMounted(() => {
    fetchProject()
    pollActiveTasks()
})

onUnmounted(() => {
    if (taskPollingInterval.value) clearInterval(taskPollingInterval.value)
})
</script>

<style scoped>
.project-view {
    padding: 20px;
    height: 100vh;
    display: flex;
    flex-direction: column;
}
</style>