<template>
  <el-dialog 
    :model-value="visible" 
    @update:model-value="emit('update:visible', $event)"
    title="Export Comic" 
    width="30%"
  >
    <span>Confirm export of current project comic?</span>
    <div class="mt-2">
      <el-checkbox v-model="splitImages">Auto-split 4-panel storyboard (1:1 split)</el-checkbox>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="emit('update:visible', false)">Cancel</el-button>
        <el-button type="primary" @click="confirmExport" :loading="loading">Confirm Export</el-button>
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
  projectId: [String, Number]
})

const emit = defineEmits(['update:visible'])

const splitImages = ref(false)
const loading = ref(false)

const confirmExport = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/api/v1/export/${props.projectId}`, {
      params: { split_images: splitImages.value }
    })
    window.open(res.data.download_url, '_blank')
    emit('update:visible', false)
    ElMessage.success('Export download started')
  } catch (error) {
    ElMessage.error('Export failed: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.mt-2 { margin-top: 10px; }
</style>