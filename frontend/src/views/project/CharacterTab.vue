<template>
  <div class="character-tab">
    <div class="mb-2 flex-row-between">
      <div class="left-actions">
        <el-popconfirm 
            title="This will regenerate ALL character images, overwriting existing ones. Continue?" 
            confirm-button-text="Yes, Overwrite" 
            cancel-button-text="Cancel"
            @confirm="generateAllCharacters"
        >
          <template #reference>
            <el-button type="primary" size="large" :disabled="!project.characters.length || isTaskRunning">
              Draw All Characters (Overwrite)
            </el-button>
          </template>
        </el-popconfirm>

        <el-button @click="emit('open-merge-dialog')" size="large" :disabled="project.characters.length < 2">
          Merge Characters
        </el-button>
      </div>
    </div>
    
    <el-container class="char-studio-container">
      <el-aside width="250px" class="char-list-aside">
        <el-menu 
          :default-active="activeCharId" 
          @select="handleCharSelect"
          background-color="#1e1e1e"
          text-color="#fff"
          active-text-color="#409EFF"
          class="char-menu"
        >
          <el-menu-item v-for="char in project.characters" :key="char.id" :index="String(char.id)">
            <span class="text-truncate">{{ char.name }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-main class="char-main">
        <div v-if="selectedChar" class="char-detail">
          <div class="char-header">
            <h2>{{ selectedChar.name }}</h2>
            <div class="header-actions">
              <el-popconfirm title="Are you sure you want to delete this character?" @confirm="deleteCharacter(selectedChar.id)">
                <template #reference>
                  <el-button type="danger" plain>Delete</el-button>
                </template>
              </el-popconfirm>
              <el-button @click="emit('open-history', 'character', selectedChar.id)">History</el-button>
              <el-button type="primary" @click="generateCharacter(selectedChar.id)" :loading="loading">
                Draw / Redraw (Background)
              </el-button>
            </div>
          </div>
          
          <el-row :gutter="24">
            <!-- Left: Attributes -->
            <el-col :xs="24" :sm="10" :md="8" :lg="8">
              <div class="info-card">
                <div class="info-header">
                  <h4>Character Attributes</h4>
                  <el-button size="small" type="primary" link @click="openJsonEditor">Edit JSON</el-button>
                </div>
                
                <el-scrollbar max-height="600px">
                  <div v-if="Object.keys(displayData).length" class="attributes-list">
                    <div v-for="(value, key) in displayData" :key="key" class="attr-wrapper">
                      
                      <!-- Complex Data (Array or Object) -->
                      <div v-if="isComplex(value)" class="complex-attr">
                          <div class="complex-label">{{ formatKey(key) }}</div>
                          
                          <!-- Array -->
                          <div v-if="Array.isArray(value)" class="array-list">
                              <div v-for="(item, idx) in value" :key="idx" class="array-item">
                                  <template v-if="isComplex(item)">
                                      <div v-for="(v, k) in item" :key="k" class="nested-item">
                                          <span class="nested-label">{{ formatKey(k) }}:</span>
                                          <span class="nested-value">{{ v }}</span>
                                      </div>
                                  </template>
                                  <template v-else>{{ item }}</template>
                              </div>
                          </div>
                          
                          <!-- Object -->
                          <div v-else class="object-grid">
                               <div v-for="(v, k) in value" :key="k" class="grid-item">
                                  <span class="nested-label">{{ formatKey(k) }}:</span>
                                  <span class="nested-value">{{ v }}</span>
                               </div>
                          </div>
                      </div>

                      <!-- Simple Data -->
                      <div v-else class="attr-item">
                        <span class="attr-label">{{ formatKey(key) }}:</span>
                        <span class="attr-value">{{ value }}</span>
                      </div>

                    </div>
                  </div>
                  <div v-else class="text-gray p-2">
                    No structured attributes found. Click Edit JSON to add details.
                  </div>
                  
                  <div v-if="selectedChar.data?.description" class="mt-4">
                     <span class="attr-label">Description:</span>
                     <p class="desc-text">{{ selectedChar.data.description }}</p>
                  </div>
                </el-scrollbar>
              </div>
            </el-col>
            
            <!-- Right: Preview -->
            <el-col :xs="24" :sm="14" :md="16" :lg="16">
              <div class="preview-card">
                <h4>Character Preview</h4>
                <div class="image-wrapper">
                  <el-image 
                    v-if="selectedChar.image_url" 
                    :src="`${selectedChar.image_url}?v=${imageVersion}`" 
                    fit="contain" 
                    class="image-preview"
                    :preview-src-list="[`${selectedChar.image_url}?v=${imageVersion}`]"
                  >
                    <template #error>
                      <div class="image-slot">
                        <el-icon><icon-picture /></el-icon>
                      </div>
                    </template>
                  </el-image>
                  <div v-else class="no-image">
                    <span>No Image Generated</span>
                    <span class="sub-text">Click "Draw / Redraw" to generate</span>
                  </div>
                </div>

                <div v-if="selectedChar.image_url" class="image-actions mt-2" style="text-align: center;">
                    <a :href="selectedChar.image_url" :download="`${selectedChar.name}.png`" target="_blank">
                      <el-button size="small" type="info" plain>Download Image</el-button>
                    </a>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        <div v-else class="empty-state">
          <el-empty description="Select a character to view details" />
        </div>
      </el-main>
    </el-container>

    <JsonEditorDialog 
      v-model:visible="showJsonEditor" 
      :content="characterEditor" 
      :title="`Edit ${selectedChar?.name || 'Character'}`"
      @save="handleJsonSave"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Picture as IconPicture } from '@element-plus/icons-vue'
import JsonEditorDialog from './JsonEditorDialog.vue'

const props = defineProps({
  project: Object,
  projectId: [String, Number],
  isTaskRunning: Boolean,
  imageVersion: Number
})

const emit = defineEmits(['task-started', 'refresh-project', 'open-merge-dialog', 'open-history'])

const activeCharId = ref('')
const characterEditor = ref('')
const loading = ref(false)
const showJsonEditor = ref(false)

const selectedChar = computed(() => {
  if (!activeCharId.value) return null
  return props.project.characters.find(c => String(c.id) === activeCharId.value)
})

const displayData = computed(() => {
  if (!selectedChar.value || !selectedChar.value.data) return {}
  const data = selectedChar.value.data
  const ignoredKeys = ['description', 'id', 'name', 'image_url', 'created_at']
  const result = {}
  for (const key in data) {
    if (ignoredKeys.includes(key)) continue
    if (data[key] !== null && data[key] !== undefined) {
        result[key] = data[key]
    }
  }
  return result
})

const isComplex = (val) => {
    return typeof val === 'object' && val !== null
}

watch(() => props.project.characters, (newChars) => {
  if (newChars && newChars.length > 0 && !activeCharId.value) {
    activeCharId.value = String(newChars[0].id)
  }
}, { immediate: true })

watch(selectedChar, (newChar) => {
  if (newChar) {
    characterEditor.value = JSON.stringify(newChar.data, null, 2)
  } else {
    characterEditor.value = ''
  }
})

const handleCharSelect = (index) => {
  activeCharId.value = index
}

const formatKey = (key) => {
  // Convert snake_case or camelCase to Title Case
  return key.replace(/([A-Z])/g, ' $1')
            .replace(/^./, str => str.toUpperCase())
            .replace(/_/g, ' ')
}

const openJsonEditor = () => {
  if (!selectedChar.value) return
  // Ensure editor has latest data
  characterEditor.value = JSON.stringify(selectedChar.value.data, null, 2)
  showJsonEditor.value = true
}

const handleJsonSave = async (newContent) => {
  characterEditor.value = newContent
  await updateCharacter(selectedChar.value.id)
}

const updateCharacter = async (charId) => {
  try {
    const data = JSON.parse(characterEditor.value)
    await axios.put(`/api/v1/projects/${props.projectId}/characters/${charId}`, data)
    ElMessage.success('Character setting saved')
    emit('refresh-project')
  } catch (e) {
    ElMessage.error('JSON format error or save failed: ' + e.message)
  }
}

const generateCharacter = async (charId) => {
  try {
    await axios.post(`/api/v1/generate/character/${charId}`)
    emit('task-started')
    ElMessage.info('Character drawing task started in background...')
  } catch (error) {
    console.error(error)
    ElMessage.error('Generation failed: ' + (error.response?.data?.detail || error.message))
  }
}

const generateAllCharacters = async () => {
  try {
    await axios.post(`/api/v1/generate/all-characters/${props.projectId}`)
    emit('task-started')
    ElMessage.info('Batch character drawing task started in background...')
  } catch (error) {
    ElMessage.error('Failed to start task: ' + (error.response?.data?.detail || error.message))
  }
}

const deleteCharacter = async (charId) => {
  try {
    await axios.delete(`/api/v1/projects/${props.projectId}/characters/${charId}`)
    ElMessage.success('Character deleted')
    if (activeCharId.value === String(charId)) {
      activeCharId.value = ''
    }
    emit('refresh-project')
  } catch (e) {
    ElMessage.error('Delete failed')
  }
}
</script>

<style scoped>
.flex-row-between {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.left-actions {
    display: flex;
    gap: 12px;
}
.char-studio-container {
    height: calc(100vh - 200px); /* Dynamic height based on viewport */
    min-height: 600px;
    border: 1px solid #333;
    background: #1e1e1e;
    border-radius: 8px;
    overflow: hidden;
}
.char-list-aside {
    background-color: #1a1a1a;
    border-right: 1px solid #333;
}
.char-menu {
    border-right: none;
    background-color: transparent;
}
.char-main {
    padding: 24px;
    overflow-y: auto;
}
.char-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #333;
}
.header-actions {
    display: flex;
    gap: 12px;
}
.info-card, .preview-card {
    background: #252525;
    border-radius: 8px;
    padding: 20px;
    height: 100%;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
}
.info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}
.info-header h4, .preview-card h4 {
    margin: 0;
    color: #eee;
    font-size: 1.1rem;
}
.attributes-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.attr-item {
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid #333;
    padding-bottom: 8px;
}
.attr-label {
    color: #909399;
    font-weight: 500;
}
.attr-value {
    color: #E5EAF3;
    text-align: right;
    max-width: 60%;
    white-space: pre-wrap;
    word-break: break-word;
}
.desc-text {
    color: #ccc;
    line-height: 1.6;
    margin-top: 8px;
    font-size: 0.95rem;
}
.image-wrapper {
    margin-top: 16px;
    width: 100%;
    /* Flexible height container */
    min-height: 400px;
    display: flex;
    justify-content: center;
    background: #1a1a1a;
    border-radius: 4px;
    padding: 10px;
}
.image-preview {
    width: 100%;
    height: auto; /* Allow height to grow */
    display: block;
}
.no-image {
    width: 100%;
    height: 400px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: #2a2a2a;
    color: #666;
    border-radius: 4px;
    gap: 10px;
}
.sub-text {
    font-size: 0.8rem;
    color: #555;
}
.text-truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: block;
}
.mb-2 { margin-bottom: 16px; }
.mt-4 { margin-top: 24px; }

/* Complex Attributes Styling */
.complex-attr {
    margin-bottom: 16px;
    background: #2a2a2a;
    border-radius: 6px;
    padding: 10px;
}
.complex-label {
    color: #409EFF;
    font-weight: 600;
    margin-bottom: 8px;
    font-size: 0.95rem;
    border-bottom: 1px solid #333;
    padding-bottom: 4px;
}
.array-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.array-item {
    background: #333;
    padding: 8px;
    border-radius: 4px;
    font-size: 0.9em;
}
.object-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 6px;
}
.nested-item {
    margin-bottom: 4px;
}
.nested-label {
    color: #bbb;
    font-weight: 500;
    margin-right: 4px;
}
.nested-value {
    color: #eee;
}
</style>