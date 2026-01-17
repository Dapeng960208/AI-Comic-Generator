<template>
  <el-dialog 
    :model-value="visible" 
    @update:model-value="emit('update:visible', $event)"
    title="Merge Characters" 
    width="40%"
    @open="resetForm"
  >
    <div class="merge-container">
      <p class="mb-2">Merge duplicate characters into a target character. Merged characters will be deleted, and character names in the storyboard will be automatically updated to the target character.</p>
      
      <el-form label-width="120px">
        <el-form-item label="Keep Character">
          <el-select v-model="mergeTargetId" placeholder="Select character to keep (Target)" style="width: 100%">
            <el-option v-for="c in characters" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="Merge Source">
          <el-select v-model="mergeSourceIds" multiple placeholder="Select characters to merge (Will be deleted)" style="width: 100%">
            <el-option 
              v-for="c in characters" 
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
        <el-button @click="emit('update:visible', false)">Cancel</el-button>
        <el-button type="primary" @click="confirmMerge" :disabled="!mergeTargetId || !mergeSourceIds.length" :loading="loading">Confirm Merge</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: Boolean,
  characters: Array,
  projectId: [String, Number]
})

const emit = defineEmits(['update:visible', 'merged'])

const mergeTargetId = ref(null)
const mergeSourceIds = ref([])
const loading = ref(false)

const resetForm = () => {
  mergeTargetId.value = null
  mergeSourceIds.value = []
}

const confirmMerge = async () => {
  loading.value = true
  try {
    await axios.post(`/api/v1/projects/${props.projectId}/characters/merge`, {
      target_char_id: mergeTargetId.value,
      source_char_ids: mergeSourceIds.value
    })
    ElMessage.success('Merge successful')
    emit('update:visible', false)
    emit('merged', { targetId: mergeTargetId.value, sourceIds: mergeSourceIds.value })
  } catch (e) {
    ElMessage.error('Merge failed: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.mb-2 { margin-bottom: 10px; }
</style>