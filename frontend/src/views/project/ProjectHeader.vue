<template>
  <div class="header">
    <h2>{{ title }}</h2>
    <div class="actions">
      <el-button type="success" @click="emit('export')">Export Comic</el-button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String
})
const emit = defineEmits(['export'])
</script>

<style scoped>
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.actions {
    display: flex;
    gap: 10px;
}
</style>