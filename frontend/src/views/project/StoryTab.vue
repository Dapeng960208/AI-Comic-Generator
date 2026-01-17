<template>
  <div class="story-tab-content">
    <!-- Top Section: Settings -->
    <el-card class="box-card mb-4" shadow="never">
      <template #header>
        <div class="card-header">
          <span>Project Configuration</span>
          <el-button type="primary" link @click="openGlobalConfig">Advanced Config (JSON)</el-button>
        </div>
      </template>
      <el-form :model="project" label-width="120px" class="settings-form" :inline="true">
        <el-form-item label="Theme">
          <el-input v-model="project.theme" placeholder="e.g. Cyberpunk" @change="saveSettings" class="w-200" />
        </el-form-item>
        <el-form-item label="Language">
          <el-select v-model="project.language" placeholder="Select" @change="saveSettings" class="w-200">
            <el-option label="Simplified Chinese" value="zh-CN" />
            <el-option label="English" value="en-US" />
            <el-option label="Japanese" value="ja-JP" />
          </el-select>
        </el-form-item>
        <el-form-item label="Panels">
          <el-input-number v-model="project.panel_count" :min="1" :max="100" @change="saveSettings" class="w-150" />
        </el-form-item>
        <el-form-item label="Aspect Ratio">
          <el-select v-model="project.aspect_ratio" placeholder="Select" @change="saveSettings" class="w-150">
            <el-option label="1:1" value="1:1" />
            <el-option label="2:3" value="2:3" />
            <el-option label="3:2" value="3:2" />
            <el-option label="3:4" value="3:4" />
            <el-option label="4:3" value="4:3" />
            <el-option label="4:5" value="4:5" />
            <el-option label="5:4" value="5:4" />
            <el-option label="9:16" value="9:16" />
            <el-option label="16:9" value="16:9" />
            <el-option label="21:9" value="21:9" />
          </el-select>
        </el-form-item>
        <el-form-item label="Resolution">
          <el-select v-model="project.resolution" placeholder="Select" @change="saveSettings" class="w-150">
            <el-option label="1K" value="1K" />
            <el-option label="2K" value="2K" />
            <el-option label="4K" value="4K" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Main Section: Story Input -->
    <el-card class="box-card story-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>Story Input</span>
          <div class="upload-area">
            <input type="file" ref="fileInput" @change="handleFileUpload" accept=".txt" style="display: none" />
            <el-button size="small" @click="$refs.fileInput.click()">Import from File (.txt)</el-button>
            <span v-if="fileName" class="file-name ml-2">{{ fileName }}</span>
          </div>
        </div>
      </template>
      
      <el-input 
        type="textarea" 
        :rows="15" 
        v-model="storyInput" 
        placeholder="Enter your story idea, synopsis, or full text here..." 
        @change="saveStoryInput" 
        class="story-textarea"
        resize="none"
      />
      
      <div class="action-footer mt-4">
        <el-button size="large" type="primary" @click="generateStoryboard" :disabled="isTaskRunning || !storyInput">
          Generate Storyboard
        </el-button>
        
        <el-popconfirm 
          title="Regenerate will overwrite existing storyboard and character settings. Continue?" 
          confirm-button-text="Yes"
          cancel-button-text="No"
          @confirm="generateStoryboard"
        >
          <template #reference>
            <el-button size="large" type="warning" plain :disabled="isTaskRunning || !storyInput">
              Regenerate All
            </el-button>
          </template>
        </el-popconfirm>

        <el-button size="large" @click="saveStoryInput">Save Story Only</el-button>
      </div>
    </el-card>

    <!-- Dialogs -->
    <JsonEditorDialog 
      v-model:visible="showGlobalConfig" 
      :content="globalConfigEditor" 
      title="Global Configuration"
      @save="handleGlobalConfigSave"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import JsonEditorDialog from './JsonEditorDialog.vue'

const props = defineProps({
  project: Object,
  projectId: [String, Number],
  isTaskRunning: Boolean
})

const emit = defineEmits(['refresh-project', 'task-started'])

const storyInput = ref('')
const fileName = ref('')
const fileInput = ref(null)
const globalConfigEditor = ref('')
const showGlobalConfig = ref(false)

// Initialize local state when project changes
watch(() => props.project, (newVal) => {
  if (newVal) {
    if (newVal.story_input && !storyInput.value) storyInput.value = newVal.story_input
    if (newVal.global_config) {
      globalConfigEditor.value = JSON.stringify(newVal.global_config.data, null, 2)
    }
  }
}, { immediate: true, deep: true })

const saveSettings = async () => {
  try {
    await axios.put(`/api/v1/projects/${props.projectId}`, { 
      theme: props.project.theme,
      language: props.project.language,
      panel_count: props.project.panel_count,
      aspect_ratio: props.project.aspect_ratio,
      resolution: props.project.resolution
    })
    ElMessage.success('Settings saved')
  } catch (e) {
    ElMessage.error('Failed to save settings')
  }
}

const saveStoryInput = async () => {
  try {
    await axios.put(`/api/v1/projects/${props.projectId}`, { story_input: storyInput.value })
    ElMessage.success('Story saved')
  } catch (e) {
    console.error("Failed to save story input", e)
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
    await axios.post(`/api/v1/generate/storyboard/${props.projectId}`, {
      user_input: storyInput.value
    })
    emit('task-started')
    ElMessage.info('Storyboard generation task started in background...')
  } catch (error) {
    ElMessage.error('Failed to start task: ' + (error.response?.data?.detail || error.message))
  }
}

const openGlobalConfig = () => {
  // Ensure editor has latest
  if (props.project.global_config) {
    globalConfigEditor.value = JSON.stringify(props.project.global_config.data, null, 2)
  } else {
    globalConfigEditor.value = '{}'
  }
  showGlobalConfig.value = true
}

const handleGlobalConfigSave = async (newContent) => {
  try {
    const data = JSON.parse(newContent)
    await axios.put(`/api/v1/projects/${props.projectId}/global_config`, data)
    ElMessage.success('Global config synced')
    emit('refresh-project')
  } catch (e) {
    ElMessage.error('Save failed: ' + e.message)
  }
}
</script>

<style scoped>
.story-tab-content {
  max-width: 1200px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.settings-form {
  /* padding: 10px 0; */
}
.w-200 { width: 200px; }
.w-150 { width: 150px; }

.story-textarea :deep(.el-textarea__inner) {
  font-family: inherit;
  font-size: 1.05rem;
  line-height: 1.6;
  padding: 16px;
}
.upload-area { display: flex; align-items: center; }
.file-name { color: #888; font-size: 0.9em; }
.action-footer {
  display: flex;
  gap: 16px;
  justify-content: flex-start;
  border-top: 1px solid #333;
  padding-top: 20px;
}

.mb-4 { margin-bottom: 24px; }
.mt-4 { margin-top: 24px; }
.ml-2 { margin-left: 10px; }
</style>