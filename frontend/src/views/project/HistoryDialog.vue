<template>
  <el-dialog 
    :model-value="visible" 
    @update:model-value="emit('update:visible', $event)"
    title="Generation History" 
    width="60%"
    @open="loadHistory"
  >
    <div class="history-list" v-loading="loading">
      <div v-for="h in historyList" :key="h.id" class="history-item" @click="selectHistoryImage(h)" :class="{ active: isCurrentHistory(h) }">
        <el-image :src="h.image_url" fit="cover" class="history-img" />
        <div class="history-meta">
          <span class="history-time">{{ new Date(h.created_at + 'Z').toLocaleString() }}</span>
          <el-tag size="small" v-if="isCurrentHistory(h)" type="success">Current</el-tag>
        </div>
      </div>
      <div v-if="historyList.length === 0 && !loading" class="empty-history">No History</div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: Boolean,
  type: String, // 'character' or 'panel'
  entityId: [String, Number],
  currentImageUrl: String
})

const emit = defineEmits(['update:visible', 'image-selected'])

const loading = ref(false)
const historyList = ref([])

const loadHistory = async () => {
  if (!props.type || !props.entityId) return
  loading.value = true
  try {
    const res = await axios.get(`/api/v1/history/${props.type}/${props.entityId}`)
    historyList.value = res.data
  } catch (e) {
    ElMessage.error('Failed to load history')
  } finally {
    loading.value = false
  }
}

const selectHistoryImage = async (historyItem) => {
  try {
    await axios.post(`/api/v1/history/select/${historyItem.id}`)
    ElMessage.success('Image switched')
    emit('update:visible', false)
    emit('image-selected')
  } catch (e) {
    ElMessage.error('Switch failed')
  }
}

const isCurrentHistory = (h) => {
  return h.image_url === props.currentImageUrl
}
</script>

<style scoped>
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
</style>