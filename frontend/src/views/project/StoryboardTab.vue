<template>
  <div class="storyboard-tab">
    <div class="comic-actions mb-4">
        <el-tooltip :disabled="hasCharacters" content="Please generate character images in Character Studio first" placement="top">
          <div style="display: inline-block;">
            <el-popconfirm 
                title="This will regenerate ALL panel images, overwriting existing ones. Continue?" 
                confirm-button-text="Yes, Overwrite" 
                cancel-button-text="Cancel"
                @confirm="generateAllImages"
            >
              <template #reference>
                <el-button type="primary" size="large" :disabled="!hasCharacters || isTaskRunning">
                  Generate All Panels (Overwrite)
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </el-tooltip>
      <div class="info-group">
        <span class="tip-text ml-2">Generation will proceed in storyboard order, subsequent panels will reference previous image content.</span>
        <span v-if="!hasCharacters" class="warning-text ml-2"><el-icon><Warning /></el-icon> Please generate characters first!</span>
      </div>
    </div>
    
    <div v-for="item in sortedStoryboard" :key="item.id" class="comic-row">
      <el-card class="panel-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="panel-title">Panel {{ item.sequence }}</span>
            <div class="header-actions">
              <el-button size="small" type="primary" link @click="openJsonEditor(item)">Edit JSON</el-button>
              <el-tooltip :disabled="hasCharacters" content="Please generate character images in Character Studio first" placement="top">
                <el-button size="small" type="primary" plain @click="generatePanel(item.id)" :disabled="!hasCharacters">Regenerate</el-button>
              </el-tooltip>
            </div>
          </div>
        </template>
        <el-row :gutter="24">
          <!-- Left: Panel Details -->
          <el-col :xs="24" :sm="10" :md="8" :lg="8">
            <div class="panel-details">
              <!-- Scene Info -->
              <div class="detail-group" v-if="item.data.scene">
                <label>Scene:</label>
                <div class="detail-content">{{ item.data.scene }}</div>
              </div>

              <!-- Action Info -->
              <div class="detail-group" v-if="item.data.action">
                <label>Action:</label>
                <div class="detail-content">{{ item.data.action }}</div>
              </div>

              <!-- Dialogue Info -->
              <div class="detail-group" v-if="item.data.dialogue">
                <label>Dialogue:</label>
                <div class="detail-content">{{ item.data.dialogue }}</div>
              </div>

              <!-- Prompt (Existing) -->
              <div class="detail-group mt-3">
                <label>Full Prompt:</label>
                <div class="detail-content prompt-text">
                  {{ item.data.prompt || 'No prompt set' }}
                </div>
              </div>
              
              <div class="detail-group mt-3" v-if="item.data.negative_prompt">
                <label>Negative Prompt:</label>
                <div class="detail-content sm-text text-gray">
                  {{ item.data.negative_prompt }}
                </div>
              </div>

              <div class="detail-group mt-3">
                <label>Included Characters:</label>
                <div class="detail-content">
                  <div v-if="getPanelCharacters(item.id).length" class="tags-wrapper">
                    <el-tag v-for="name in getPanelCharacters(item.id)" :key="name" size="small" effect="dark">{{ name }}</el-tag>
                  </div>
                  <span v-else class="text-gray sm-text">No explicit characters</span>
                </div>
              </div>
            </div>
          </el-col>
          
          <!-- Right: Image Preview -->
          <el-col :xs="24" :sm="14" :md="16" :lg="16">
            <div class="image-area">
              <div class="image-wrapper">
                <el-image 
                  v-if="item.image_url" 
                  :src="`${item.image_url}?v=${imageVersion}`" 
                  fit="contain" 
                  class="comic-preview"
                  :preview-src-list="[`${item.image_url}?v=${imageVersion}`]"
                >
                  <template #error>
                    <div class="image-slot">
                      <el-icon><icon-picture /></el-icon>
                    </div>
                  </template>
                </el-image>
                <div v-else class="no-image">
                  <span>No Image Generated</span>
                </div>
              </div>
              
              <div v-if="item.image_url" class="image-actions mt-2">
                <a :href="item.image_url" :download="`panel_${item.sequence}.png`" target="_blank" class="mr-2">
                  <el-button size="small" type="info" plain>Download</el-button>
                </a>
                <el-button size="small" @click="emit('open-history', 'panel', item.id)">History</el-button>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <JsonEditorDialog 
      v-model:visible="showJsonEditor" 
      :content="currentEditorContent" 
      :title="`Edit Panel ${currentEditingItem?.sequence || ''}`"
      @save="handleJsonSave"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Warning, Picture as IconPicture } from '@element-plus/icons-vue'
import JsonEditorDialog from './JsonEditorDialog.vue'

const props = defineProps({
  project: Object,
  projectId: [String, Number],
  isTaskRunning: Boolean,
  imageVersion: Number
})

const emit = defineEmits(['task-started', 'refresh-project', 'open-history'])

const showJsonEditor = ref(false)
const currentEditingItem = ref(null)
const currentEditorContent = ref('')

const sortedStoryboard = computed(() => {
  if (!props.project.storyboard_items) return []
  return [...props.project.storyboard_items].sort((a, b) => a.sequence - b.sequence)
})

const hasCharacters = computed(() => {
  if (!props.project.characters) return false
  return props.project.characters.some(c => c.image_url)
})

const getPanelCharacters = (itemId) => {
  const item = props.project.storyboard_items.find(i => i.id === itemId)
  if (!item || !item.data.characters) return []
  
  let chars = item.data.characters
  if (typeof chars === 'string') return [chars]
  if (Array.isArray(chars)) {
    return chars.map(c => typeof c === 'string' ? c : c.name)
  }
  return []
}

const openJsonEditor = (item) => {
  currentEditingItem.value = item
  currentEditorContent.value = JSON.stringify(item.data, null, 2)
  showJsonEditor.value = true
}

const handleJsonSave = async (newContent) => {
  if (!currentEditingItem.value) return
  try {
    const data = JSON.parse(newContent)
    await axios.put(`/api/v1/projects/${props.projectId}/storyboard/${currentEditingItem.value.id}`, data)
    ElMessage.success('Storyboard content saved')
    emit('refresh-project')
  } catch (e) {
    ElMessage.error('JSON format error or save failed: ' + e.message)
  }
}

const generateAllImages = async () => {
  try {
    await axios.post(`/api/v1/generate/all-images/${props.projectId}`)
    emit('task-started')
    ElMessage.info('Full image generation task started in background...')
  } catch (error) {
    ElMessage.error('Failed to start task: ' + (error.response?.data?.detail || error.message))
  }
}

const generatePanel = async (itemId) => {
  try {
    await axios.post(`/api/v1/generate/panel/${itemId}`)
    emit('task-started')
    ElMessage.info('Panel drawing task started in background...')
  } catch (error) {
    console.error(error)
    ElMessage.error('Failed to start task: ' + (error.response?.data?.detail || error.message))
  }
}
</script>

<style scoped>
.storyboard-tab {
  padding-bottom: 40px;
}
.comic-actions {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}
.info-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.comic-row {
    margin-bottom: 24px;
}
.panel-card {
    border: 1px solid #333;
    background-color: #1e1e1e;
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.panel-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #409EFF;
}
.header-actions {
    display: flex;
    gap: 10px;
}
.panel-details {
    padding-right: 16px;
}
.detail-group {
    margin-bottom: 12px;
}
.detail-group label {
    display: block;
    color: #909399;
    font-size: 0.9rem;
    margin-bottom: 4px;
    font-weight: 500;
}
.detail-content {
    color: #E5EAF3;
    line-height: 1.5;
}
.prompt-text {
    background: #252525;
    padding: 10px;
    border-radius: 4px;
    font-size: 0.95rem;
    max-height: 200px;
    overflow-y: auto;
}
.tags-wrapper {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.image-area {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.image-wrapper {
    width: 100%;
    /* Flexible height */
    min-height: 300px;
    display: flex;
    justify-content: center;
    background: #1a1a1a;
    border-radius: 4px;
    padding: 10px;
}
.comic-preview {
    width: 100%;
    height: auto;
    display: block;
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
.image-actions {
    display: flex;
    justify-content: center;
    width: 100%;
}
.tip-text { color: #888; font-size: 0.9em; }
.warning-text { color: #E6A23C; font-size: 0.9em; display: inline-flex; align-items: center; gap: 4px; }
.text-gray { color: #888; }
.sm-text { font-size: 0.85em; }
.mt-2 { margin-top: 10px; }
.mt-3 { margin-top: 16px; }
.mb-4 { margin-bottom: 24px; }
.ml-2 { margin-left: 10px; }
.mr-2 { margin-right: 10px; }
</style>