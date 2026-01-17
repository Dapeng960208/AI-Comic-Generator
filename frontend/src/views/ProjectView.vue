<template>
  <div class="project-view" v-loading="loading" element-loading-text="Processing..." element-loading-background="rgba(0, 0, 0, 0.8)">
    <div class="header">
      <h2>{{ project.title }}</h2>
      <div class="actions">
          <el-button type="success" @click="openExportDialog">Export Comic</el-button>
      </div>
    </div>

    <!-- Task Manager (Side/Bottom Panel) -->
    <div v-if="activeTasks.length > 0" class="task-manager" :class="{ collapsed: isTaskManagerCollapsed }">
        <div class="task-header" @click="isTaskManagerCollapsed = !isTaskManagerCollapsed">
            <span>Background Tasks ({{ runningTasksCount }})</span>
            <el-icon><component :is="isTaskManagerCollapsed ? 'ArrowUp' : 'ArrowDown'" /></el-icon>
        </div>
        <div v-show="!isTaskManagerCollapsed" class="task-list">
            <div v-for="task in activeTasks" :key="task.id" class="task-item">
                 <div class="task-info">
                     <div class="task-name-group">
                        <span class="task-name" :title="task.description">{{ task.name || getTaskTypeName(task.type) }}</span>
                        <span class="task-desc" v-if="task.description">{{ task.description }}</span>
                        <span class="task-error" v-if="task.status === 'failed' && task.message" :title="task.message">
                            Failure Reason: {{ task.message }}
                        </span>
                     </div>
                     <span class="task-status" :class="task.status">{{ getTaskStatusText(task.status) }}</span>
                 </div>
                 <el-progress :percentage="task.progress" :status="getTaskProgressStatus(task.status)" :stroke-width="6"></el-progress>
            </div>
        </div>
    </div>

    <el-tabs v-model="activeTab" class="workflow-tabs">
      <!-- Tab 1: Story & JSON -->
      <el-tab-pane label="1. Story & Config" name="story">
        <el-row :gutter="20">
          <el-col :span="10">
            <h3>Generation Settings</h3>
            <el-form :model="project" label-width="140px" class="settings-form">
                <el-form-item label="Theme">
                    <el-input v-model="project.theme" placeholder="e.g. Cyberpunk, Fantasy" @change="saveSettings" />
                </el-form-item>
                <el-form-item label="Language">
                    <el-select v-model="project.language" placeholder="Select Language" @change="saveSettings">
                        <el-option label="Simplified Chinese" value="zh-CN" />
                        <el-option label="English" value="en-US" />
                        <el-option label="Japanese" value="ja-JP" />
                    </el-select>
                </el-form-item>
                <el-form-item label="Estimated Panels">
                    <el-input-number v-model="project.panel_count" :min="1" :max="100" @change="saveSettings" />
                </el-form-item>
                <el-form-item label="Aspect Ratio">
                    <el-select v-model="project.aspect_ratio" placeholder="Select Ratio" @change="saveSettings">
                        <el-option label="16:9 (Landscape)" value="16:9" />
                        <el-option label="9:16 (Portrait)" value="9:16" />
                        <el-option label="1:1 (Square)" value="1:1" />
                        <el-option label="4:3" value="4:3" />
                        <el-option label="3:4" value="3:4" />
                    </el-select>
                </el-form-item>
            </el-form>

            <h3>Story Input</h3>
             <div class="upload-area mb-2">
                <input type="file" ref="fileInput" @change="handleFileUpload" accept=".txt" style="display: none" />
                <el-button @click="$refs.fileInput.click()">Upload Novel File (.txt)</el-button>
                <span v-if="fileName" class="file-name">{{ fileName }}</span>
            </div>
            <el-input type="textarea" :rows="15" v-model="storyInput" placeholder="Enter story inspiration or upload a novel file..." @change="saveStoryInput" />
            <div class="button-group mt-2">
                <el-button type="primary" @click="generateStoryboard" :disabled="isTaskRunning">Generate Storyboard Config (Background)</el-button>
                <el-popconfirm title="Are you sure you want to regenerate? This will overwrite all current configurations and storyboard scripts." @confirm="generateStoryboard">
                    <template #reference>
                        <el-button type="warning" :disabled="isTaskRunning">Regenerate All Configs</el-button>
                    </template>
                </el-popconfirm>
                <el-button @click="saveStoryInput" size="small">Save Story</el-button>
            </div>
          </el-col>
          <el-col :span="14">
            <h3>JSON Editor</h3>
            <el-collapse>
               <el-collapse-item title="Global Config" name="1">
                 <el-input 
                    type="textarea" 
                    :rows="10" 
                    v-model="editors.global_config" 
                    @change="updateGlobalConfig"
                 />
                 <el-button size="small" type="primary" class="mt-2" @click="updateGlobalConfig">Save & Sync</el-button>
               </el-collapse-item>
               <el-collapse-item title="Characters" name="2">
                 <div v-for="char in project.characters" :key="char.id" class="json-item">
                    <div class="json-header">
                        <strong>{{ char.name }}</strong>
                    </div>
                    <el-input 
                        type="textarea" 
                        :rows="6" 
                        v-model="editors.characters[char.id]" 
                    />
                    <el-button size="small" class="mt-1" @click="updateCharacter(char.id)">Save</el-button>
                 </div>
               </el-collapse-item>
               <el-collapse-item title="Storyboard" name="3">
                 <div v-for="item in sortedStoryboard" :key="item.id" class="json-item">
                    <div class="json-header">
                        <strong>Panel {{ item.sequence }}</strong>
                    </div>
                    <el-input 
                        type="textarea" 
                        :rows="6" 
                        v-model="editors.storyboard[item.id]" 
                    />
                    <el-button size="small" class="mt-1" @click="updateStoryboardItem(item.id)">Save</el-button>
                 </div>
               </el-collapse-item>
            </el-collapse>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- Tab 2: Character Studio -->
      <el-tab-pane label="2. Character Studio" name="characters">
        <div class="mb-2 flex-row-between">
             <div class="left-actions">
                <el-button type="primary" @click="generateAllCharacters" :disabled="!project.characters.length || isTaskRunning">Draw All Characters (Background)</el-button>
                <el-button @click="openMergeDialog" :disabled="project.characters.length < 2">Merge Characters</el-button>
             </div>
        </div>
        <el-container class="char-studio-container" style="height: 600px; border: 1px solid #333">
            <el-aside width="250px" style="background-color: #1e1e1e; border-right: 1px solid #333">
                <el-menu 
                    :default-active="activeCharId" 
                    @select="handleCharSelect"
                    background-color="#1e1e1e"
                    text-color="#fff"
                    active-text-color="#409EFF"
                    style="border-right: none"
                >
                    <el-menu-item v-for="char in project.characters" :key="char.id" :index="String(char.id)">
                        <span>{{ char.name }}</span>
                    </el-menu-item>
                </el-menu>
            </el-aside>
            <el-main>
                <div v-if="selectedChar" class="char-detail">
                    <div class="char-header">
                        <h2>{{ selectedChar.name }}</h2>
                        <div class="header-actions">
                            <el-popconfirm title="Are you sure you want to delete this character?" @confirm="deleteCharacter(selectedChar.id)">
                                <template #reference>
                                    <el-button type="danger" plain>Delete</el-button>
                                </template>
                            </el-popconfirm>
                            <el-button @click="openHistory('character', selectedChar.id)">History</el-button>
                            <el-button type="primary" @click="generateCharacter(selectedChar.id)" :loading="loading">Draw / Redraw (Background)</el-button>
                        </div>
                    </div>
                    <el-row :gutter="20">
                        <el-col :span="12">
                            <h4>Character Setting (JSON)</h4>
                            <el-input 
                                type="textarea" 
                                :rows="15" 
                                v-model="editors.characters[selectedChar.id]" 
                                @change="updateCharacter(selectedChar.id)"
                            />
                            <el-button class="mt-2" size="small" @click="updateCharacter(selectedChar.id)">Save Setting</el-button>
                        </el-col>
                        <el-col :span="12">
                            <h4>Character Preview</h4>
                            <div class="image-wrapper">
                                <el-image 
                                    v-if="selectedChar.image_url" 
                                    :src="selectedChar.image_url" 
                                    fit="contain" 
                                    class="image-preview"
                                    :preview-src-list="[selectedChar.image_url]"
                                />
                                <div v-else class="no-image">No Image</div>
                            </div>
                        </el-col>
                    </el-row>
                </div>
                <div v-else class="empty-state">
                    Please select a character from the left
                </div>
            </el-main>
        </el-container>
      </el-tab-pane>

      <!-- Tab 3: Comic Board -->
      <el-tab-pane label="3. Storyboard Canvas" name="comic">
        <div class="comic-actions mb-2">
            <el-tooltip :disabled="hasCharacters" content="Please generate character images in Character Studio first" placement="top">
                 <div style="display: inline-block;">
                    <el-button type="primary" size="large" @click="generateAllImages" :disabled="!hasCharacters || isTaskRunning">Generate All Panels (Background)</el-button>
                 </div>
            </el-tooltip>
             <span class="tip-text ml-2">Generation will proceed in storyboard order, subsequent panels will reference previous image content.</span>
             <span v-if="!hasCharacters" class="warning-text ml-2"><el-icon><Warning /></el-icon> Please generate characters first!</span>
        </div>
        
        <div v-for="item in sortedStoryboard" :key="item.id" class="comic-row">
          <el-card>
            <template #header>
                <div class="card-header">
                    <span>Panel {{ item.sequence }}</span>
                    <el-tooltip :disabled="hasCharacters" content="Please generate character images in Character Studio first" placement="top">
                         <el-button size="small" @click="generatePanel(item.id)" :disabled="!hasCharacters">Regenerate This Panel</el-button>
                    </el-tooltip>
                </div>
            </template>
            <el-row :gutter="20">
              <el-col :span="10">
                <div class="panel-json-display">
                    <strong>JSON Content:</strong>
                    <pre class="json-content">{{ editors.storyboard[item.id] }}</pre>
                    <el-button size="small" class="mt-1" @click="updateStoryboardItem(item.id)">Save JSON</el-button>
                    
                    <div class="included-chars mt-2">
                        <strong>Included Characters:</strong>
                        <div v-if="getPanelCharacters(item.id).length">
                             <el-tag v-for="name in getPanelCharacters(item.id)" :key="name" class="mr-1" size="small">{{ name }}</el-tag>
                        </div>
                        <span v-else class="text-gray">No explicit characters</span>
                    </div>
                </div>
              </el-col>
              <el-col :span="14">
                <div class="image-area">
                    <el-image 
                    v-if="item.image_url" 
                    :src="item.image_url" 
                    fit="contain" 
                    class="comic-preview"
                    :preview-src-list="[item.image_url]"
                    />
                    <div v-else class="no-image">No Image</div>
                    
                    <div v-if="item.image_url" class="image-actions mt-1">
                        <a :href="item.image_url" :download="`panel_${item.sequence}.png`" target="_blank">
                             <el-button size="small" type="info" plain>Download Image</el-button>
                        </a>
                        <el-button size="small" @click="openHistory('panel', item.id)" class="ml-2">History</el-button>
                    </div>
                </div>
              </el-col>
            </el-row>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Merge Dialog -->
    <el-dialog v-model="showMergeDialog" title="Merge Characters" width="40%">
        <div class="merge-container">
            <p class="mb-2">Merge duplicate characters into a target character. Merged characters will be deleted, and character names in the storyboard will be automatically updated to the target character.</p>
            
            <el-form label-width="120px">
                <el-form-item label="Keep Character">
                    <el-select v-model="mergeTargetId" placeholder="Select character to keep (Target)" style="width: 100%">
                        <el-option v-for="c in project.characters" :key="c.id" :label="c.name" :value="c.id" />
                    </el-select>
                </el-form-item>
                
                <el-form-item label="Merge Source">
                    <el-select v-model="mergeSourceIds" multiple placeholder="Select characters to merge (Will be deleted)" style="width: 100%">
                        <el-option 
                            v-for="c in project.characters" 
                            :key="c.id" 
                            :label="c.name" 
                            :value="c.id" 
                            :disabled="c.id === mergeTargetId"
                        />
                    </el-select>
                </el-form-item>
            </el-form>
        </div>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="showMergeDialog = false">Cancel</el-button>
                <el-button type="primary" @click="confirmMerge" :disabled="!mergeTargetId || !mergeSourceIds.length">Confirm Merge</el-button>
            </span>
        </template>
    </el-dialog>

    <!-- Export Dialog -->
    <el-dialog v-model="showExportDialog" title="Export Comic" width="30%">
        <span>Confirm export of current project comic?</span>
        <div class="mt-2">
            <el-checkbox v-model="splitImages">Auto-split 4-panel storyboard (1:1 split)</el-checkbox>
        </div>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="showExportDialog = false">Cancel</el-button>
                <el-button type="primary" @click="confirmExport">Confirm Export</el-button>
            </span>
        </template>
    </el-dialog>

    <!-- History Dialog -->
    <el-dialog v-model="showHistoryDialog" title="Generation History" width="60%">
        <div class="history-list">
            <div v-for="h in historyList" :key="h.id" class="history-item" @click="selectHistoryImage(h)" :class="{ active: isCurrentHistory(h) }">
                <el-image :src="h.image_url" fit="cover" class="history-img" />
                <div class="history-meta">
                    <span class="history-time">{{ new Date(h.created_at + 'Z').toLocaleString() }}</span>
                    <el-tag size="small" v-if="isCurrentHistory(h)" type="success">Current</el-tag>
                </div>
            </div>
            <div v-if="historyList.length === 0" class="empty-history">No History</div>
        </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElNotification } from 'element-plus'
import { Warning, ArrowUp, ArrowDown } from '@element-plus/icons-vue'

const route = useRoute()
const projectId = route.params.id
const project = ref({
    title: '',
    theme: '',
    language: 'zh-CN',
    panel_count: undefined,
    aspect_ratio: '16:9',
    characters: [],
    storyboard_items: []
})
const loading = ref(false)
const activeTab = ref('story')
const storyInput = ref('')
const activeTasks = ref([]) // Changed to array
const isTaskManagerCollapsed = ref(false)
const taskPollingInterval = ref(null)
const fileInput = ref(null)
const fileName = ref('')
const activeCharId = ref('')

// Export State
const showExportDialog = ref(false)
const splitImages = ref(false)

// Merge State
const showMergeDialog = ref(false)
const mergeTargetId = ref(null)
const mergeSourceIds = ref([])

// History State
const showHistoryDialog = ref(false)
const historyList = ref([])
const currentHistoryType = ref('')
const currentHistoryEntityId = ref('')

// Editors state
const editors = ref({
    global_config: '',
    characters: {},
    storyboard: {}
})

const sortedStoryboard = computed(() => {
    if (!project.value.storyboard_items) return []
    return [...project.value.storyboard_items].sort((a, b) => a.sequence - b.sequence)
})

const isTaskRunning = computed(() => {
    return activeTasks.value.some(t => ['pending', 'processing'].includes(t.status))
})

const runningTasksCount = computed(() => {
    return activeTasks.value.filter(t => ['pending', 'processing'].includes(t.status)).length
})

const hasCharacters = computed(() => {
    if (!project.value.characters) return false
    return project.value.characters.some(c => c.image_url)
})

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

const selectedChar = computed(() => {
    if (!activeCharId.value) return null
    return project.value.characters.find(c => String(c.id) === activeCharId.value)
})

const handleCharSelect = (index) => {
    activeCharId.value = index
}

const getPanelCharacters = (itemId) => {
    const item = project.value.storyboard_items.find(i => i.id === itemId)
    if (!item || !item.data.characters) return []
    
    let chars = item.data.characters
    if (typeof chars === 'string') return [chars]
    if (Array.isArray(chars)) {
        return chars.map(c => typeof c === 'string' ? c : c.name)
    }
    return []
}

const initEditors = () => {
    if (project.value.global_config) {
        editors.value.global_config = JSON.stringify(project.value.global_config.data, null, 2)
    }
    if (project.value.characters) {
        project.value.characters.forEach(char => {
            editors.value.characters[char.id] = JSON.stringify(char.data, null, 2)
        })
        if (!activeCharId.value && project.value.characters.length > 0) {
            activeCharId.value = String(project.value.characters[0].id)
        }
    }
    if (project.value.storyboard_items) {
        project.value.storyboard_items.forEach(item => {
            editors.value.storyboard[item.id] = JSON.stringify(item.data, null, 2)
        })
    }
    if (project.value.story_input) {
        storyInput.value = project.value.story_input
    }
}

const fetchProject = async () => {
    // if (!project.value.id) loading.value = true // Don't show global loading on refresh
    try {
        const res = await axios.get(`/api/v1/projects/${projectId}`)
        // Merge data to prevent flickering
        // project.value = { ...project.value, ...res.data }
        
        // Smarter update: only update what changed
        project.value.title = res.data.title
        project.value.theme = res.data.theme
        project.value.language = res.data.language
        project.value.panel_count = res.data.panel_count
        project.value.aspect_ratio = res.data.aspect_ratio
        project.value.story_input = res.data.story_input
        project.value.global_config = res.data.global_config
        
        // Update characters (keep references if possible)
        if (res.data.characters) {
            project.value.characters = res.data.characters
        }
        
        // Update storyboard items (keep references if possible)
        if (res.data.storyboard_items) {
             project.value.storyboard_items = res.data.storyboard_items
        }

        // Only init editors if first load or explicitly requested? 
        // Or if we are not editing? 
        // Let's not overwrite editors if user is typing!
        // initEditors() 
        if (!editors.value.global_config) initEditors()
        
    } catch (error) {
        console.error('Fetch project error', error)
        // ElMessage.error('无法加载项目')
    } finally {
        loading.value = false
    }
}

// Poll for all project tasks
const pollActiveTasks = async () => {
    if (taskPollingInterval.value) clearInterval(taskPollingInterval.value)
    
    taskPollingInterval.value = setInterval(async () => {
        try {
            const res = await axios.get(`/api/v1/tasks/project/${projectId}`)
            // Filter to show running tasks or recently completed (last 1 min?)
            // For simplicity, let's just show top 5 recent tasks
            activeTasks.value = res.data.slice(0, 5)
            
            // Check if we need to refresh project data (if any task just completed)
            const hasCompleted = res.data.some(t => t.status === 'completed' && (!activeTasks.value.find(old => old.id === t.id)?.status === 'completed'))
            
            // Check if any processing task has progress update or if we should refresh images
            // If tasks are processing, we should fetch project data periodically to show new images
            const anyProcessing = res.data.some(t => t.status === 'processing')
            
            if (hasCompleted || anyProcessing) {
                // If completed or processing, refresh project to show new images/status
                fetchProject()
            }
            
        } catch (e) {
            console.error("Polling error", e)
        }
    }, 2000)
}

// Watch active tasks to trigger project refresh on completion
watch(activeTasks, (newTasks, oldTasks) => {
    if (oldTasks.length === 0) return
    
    // If any task changed from processing/pending to completed
    const changed = newTasks.some(t => {
        const old = oldTasks.find(o => o.id === t.id)
        return t.status === 'completed' && old && old.status !== 'completed'
    })
    
    if (changed) {
        fetchProject()
        ElNotification({ title: 'Task Completed', message: 'Background tasks updated', type: 'success' })
    }
}, { deep: true })


const saveStoryInput = async () => {
    try {
        await axios.put(`/api/v1/projects/${projectId}`, { story_input: storyInput.value })
    } catch (e) {
        console.error("Failed to save story input", e)
    }
}

const saveSettings = async () => {
    try {
        await axios.put(`/api/v1/projects/${projectId}`, { 
            theme: project.value.theme,
            language: project.value.language,
            panel_count: project.value.panel_count,
            aspect_ratio: project.value.aspect_ratio
        })
        ElMessage.success('Settings saved')
    } catch (e) {
        ElMessage.error('Failed to save settings')
    }
}

const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (!file) return
    fileName.value = file.name
    const reader = new FileReader()
    reader.onload = (e) => {
        storyInput.value = e.target.result
        saveStoryInput() 
        ElMessage.success('File read successfully')
    }
    reader.onerror = () => ElMessage.error('Failed to read file')
    reader.readAsText(file)
}

const generateStoryboard = async () => {
    if (!storyInput.value) return ElMessage.warning('Please enter story content')
    try {
        await saveStoryInput()
        await axios.post(`/api/v1/generate/storyboard/${projectId}`, {
            user_input: storyInput.value
        })
        pollActiveTasks() // Ensure polling is active
        ElMessage.info('Storyboard generation task started in background...')
    } catch (error) {
        ElMessage.error('Failed to start task: ' + (error.response?.data?.detail || error.message))
    }
}

const generateAllImages = async () => {
    try {
        await axios.post(`/api/v1/generate/all-images/${projectId}`)
        pollActiveTasks()
        ElMessage.info('Full image generation task started in background...')
    } catch (error) {
        ElMessage.error('Failed to start task: ' + (error.response?.data?.detail || error.message))
    }
}

const updateGlobalConfig = async () => {
    try {
        const data = JSON.parse(editors.value.global_config)
        await axios.put(`/api/v1/projects/${projectId}/global_config`, data)
        ElMessage.success('Global config synced')
        await fetchProject()
    } catch (e) {
        ElMessage.error('JSON format error or save failed')
    }
}

const updateCharacter = async (charId) => {
    try {
        const data = JSON.parse(editors.value.characters[charId])
        await axios.put(`/api/v1/projects/${projectId}/characters/${charId}`, data)
        ElMessage.success('Character setting saved')
    } catch (e) {
        ElMessage.error('JSON format error or save failed')
    }
}

const updateStoryboardItem = async (itemId) => {
    try {
        const data = JSON.parse(editors.value.storyboard[itemId])
        await axios.put(`/api/v1/projects/${projectId}/storyboard/${itemId}`, data)
        ElMessage.success('Storyboard content saved')
    } catch (e) {
        ElMessage.error('JSON format error or save failed')
    }
}

const generateCharacter = async (charId) => {
    try {
        // Now returns task_id
        await axios.post(`/api/v1/generate/character/${charId}`)
        pollActiveTasks()
        ElMessage.info('Character drawing task started in background...')
    } catch (error) {
        console.error(error)
        ElMessage.error('Generation failed: ' + (error.response?.data?.detail || error.message))
    }
}

const generateAllCharacters = async () => {
    try {
        await axios.post(`/api/v1/generate/all-characters/${projectId}`)
        pollActiveTasks()
        ElMessage.info('Batch character drawing task started in background...')
    } catch (error) {
        ElMessage.error('Failed to start task: ' + (error.response?.data?.detail || error.message))
    }
}

const generatePanel = async (itemId) => {
    // Single panel generation is still sync for now, or should we make it async?
    // User said "Storyboard generation... show json... save json... download image".
    // User also said "Draw/Redraw character not using background task" -> Fixed.
    // User didn't explicitly say single panel generation must be background, but "Generate all images" is background.
    // Let's keep single panel sync for now unless user complains, as it's faster feedback for one image.
    try {
        await axios.post(`/api/v1/generate/panel/${itemId}`)
        pollActiveTasks()
        ElMessage.info('Panel drawing task started in background...')
    } catch (error) {
        console.error(error)
        ElMessage.error('Failed to start task: ' + (error.response?.data?.detail || error.message))
    }
}

const deleteCharacter = async (charId) => {
    try {
        await axios.delete(`/api/v1/projects/${projectId}/characters/${charId}`)
        ElMessage.success('Character deleted')
        // Clear selection if deleted
        if (activeCharId.value === String(charId)) {
            activeCharId.value = ''
        }
        await fetchProject()
    } catch (e) {
        ElMessage.error('Delete failed')
    }
}

const openMergeDialog = () => {
    mergeTargetId.value = null
    mergeSourceIds.value = []
    showMergeDialog.value = true
}

const confirmMerge = async () => {
    try {
        await axios.post(`/api/v1/projects/${projectId}/characters/merge`, {
            target_char_id: mergeTargetId.value,
            source_char_ids: mergeSourceIds.value
        })
        ElMessage.success('Merge successful')
        showMergeDialog.value = false
        // Reset selection if needed
        if (mergeSourceIds.value.includes(Number(activeCharId.value))) {
            activeCharId.value = String(mergeTargetId.value)
        }
        await fetchProject()
    } catch (e) {
        ElMessage.error('Merge failed: ' + (e.response?.data?.detail || e.message))
    }
}

const openExportDialog = () => {
    if (!hasCharacters.value && !project.value.storyboard_items.some(i => i.image_url)) {
        ElMessage.warning('No exportable image content')
        return
    }
    showExportDialog.value = true
}

const confirmExport = async () => {
    try {
        const res = await axios.get(`/api/v1/export/${projectId}`, {
            params: { split_images: splitImages.value }
        })
        window.open(res.data.download_url, '_blank')
        showExportDialog.value = false
        ElMessage.success('Export download started')
    } catch (error) {
        ElMessage.error('Export failed: ' + (error.response?.data?.detail || error.message))
    }
}

const openHistory = async (type, id) => {
    currentHistoryType.value = type
    currentHistoryEntityId.value = id
    try {
        const res = await axios.get(`/api/v1/history/${type}/${id}`)
        historyList.value = res.data
        showHistoryDialog.value = true
    } catch (e) {
        ElMessage.error('Failed to load history')
    }
}

const selectHistoryImage = async (historyItem) => {
    try {
        await axios.post(`/api/v1/history/select/${historyItem.id}`)
        ElMessage.success('Image switched')
        showHistoryDialog.value = false
        await fetchProject()
    } catch (e) {
        ElMessage.error('Switch failed')
    }
}

const isCurrentHistory = (h) => {
    let currentUrl = ''
    if (currentHistoryType.value === 'character') {
        const char = project.value.characters.find(c => c.id === currentHistoryEntityId.value)
        currentUrl = char?.image_url
    } else {
        const item = project.value.storyboard_items.find(i => i.id === currentHistoryEntityId.value)
        currentUrl = item?.image_url
    }
    return h.image_url === currentUrl
}

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
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.flex-row-between {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.left-actions {
    display: flex;
    gap: 10px;
}
.mt-2 { margin-top: 10px; }
.mb-2 { margin-bottom: 10px; }
.ml-2 { margin-left: 10px; }
.mr-1 { margin-right: 5px; }
.mt-1 { margin-top: 5px; }
.text-gray { color: #666; font-size: 0.9em; }
.warning-text { color: #E6A23C; font-size: 0.9em; display: inline-flex; align-items: center; gap: 4px; }

/* Task Manager */
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
    max-width: 70%;
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

.image-preview, .comic-preview {
    width: 100%;
    height: 400px;
    background: #333;
    border-radius: 4px;
}
.no-image {
    width: 100%;
    height: 300px;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #2a2a2a;
    color: #666;
    border-radius: 4px;
}
.comic-row {
    margin-bottom: 20px;
}
.json-item {
    margin-bottom: 15px;
    border-bottom: 1px solid #333;
    padding-bottom: 10px;
}
.json-header {
    margin-bottom: 5px;
    font-size: 1.1em;
    color: #409EFF;
}
.panel-info p { margin: 5px 0; color: #bbb; }
.actions { display: flex; gap: 10px; }
.button-group { display: flex; gap: 10px; align-items: center; }
.upload-area { display: flex; align-items: center; gap: 10px; }
.file-name { color: #888; font-size: 0.9em; }
.settings-form { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #333; }

.char-studio-container {
    height: 600px;
    border: 1px solid #333;
    background: #1e1e1e;
}
.char-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    border-bottom: 1px solid #333;
    padding-bottom: 10px;
}
.empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #666;
    font-size: 1.2em;
}
.json-content {
    background: #111;
    padding: 10px;
    border-radius: 4px;
    overflow: auto;
    max-height: 300px;
    font-size: 0.85em;
    color: #a6e22e;
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.tip-text { color: #888; font-size: 0.9em; }

/* History Dialog Styles */
.history-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 20px;
    max-height: 500px;
    overflow-y: auto;
    padding: 10px;
}
.history-item {
    cursor: pointer;
    border: 2px solid transparent;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
    background: #222;
    transition: all 0.2s;
}
.history-item:hover {
    border-color: #409EFF;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}
.history-item.active {
    border-color: #67C23A;
}
.history-img {
    width: 100%;
    height: 180px;
    display: block;
}
.history-meta {
    padding: 8px;
    font-size: 0.8em;
    color: #888;
    background: #1a1a1a;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 5px;
    align-items: center;
}
.empty-history {
    text-align: center;
    color: #666;
    padding: 40px;
}
.header-actions {
    display: flex;
    gap: 10px;
}
.image-actions {
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>
