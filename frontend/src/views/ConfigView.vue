<template>
  <div class="config-view">
    <div class="header">
      <h2>Model Configurations</h2>
      <el-button type="primary" @click="openDialog()">Add Config</el-button>
    </div>

    <el-table :data="configs" style="width: 100%">
      <el-table-column prop="provider" label="Provider" />
      <el-table-column prop="model_name" label="Model Name" />
      <el-table-column prop="model_type" label="Type" />
      <el-table-column prop="is_active" label="Active">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'info'">{{ scope.row.is_active ? 'Yes' : 'No' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Actions">
        <template #default="scope">
          <el-button size="small" @click="openDialog(scope.row)">Edit</el-button>
          <el-button size="small" type="danger" @click="deleteConfig(scope.row.id)">Delete</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? 'Edit Config' : 'Add Config'">
      <el-form :model="form" label-width="120px">
        <el-form-item label="Provider">
          <el-select v-model="form.provider" placeholder="Select provider">
            <el-option label="Google" value="google" />
          </el-select>
        </el-form-item>
        <el-form-item label="Model Name">
          <el-input v-model="form.model_name" placeholder="e.g. gemini-1.5-flash" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password />
        </el-form-item>
        <el-form-item label="Type">
          <el-select v-model="form.model_type">
            <el-option label="Text" value="text" />
            <el-option label="Image" value="image" />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL">
            <el-input v-model="form.base_url" placeholder="Optional" />
        </el-form-item>
        <el-form-item label="Active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="saveConfig">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const configs = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({
  provider: 'google',
  model_name: '',
  api_key: '',
  model_type: 'text',
  base_url: '',
  is_active: true
})

const fetchConfigs = async () => {
  try {
    const res = await axios.get('/api/v1/configs/')
    configs.value = res.data
  } catch (error) {
    ElMessage.error('Failed to fetch configs')
  }
}

const openDialog = (row = null) => {
  if (row) {
    isEdit.value = true
    form.value = { ...row }
  } else {
    isEdit.value = false
    form.value = {
      provider: 'google',
      model_name: '',
      api_key: '',
      model_type: 'text',
      base_url: '',
      is_active: true
    }
  }
  dialogVisible.value = true
}

const saveConfig = async () => {
  try {
    if (isEdit.value) {
      await axios.put(`/api/v1/configs/${form.value.id}`, form.value)
    } else {
      await axios.post('/api/v1/configs/', form.value)
    }
    ElMessage.success('Saved successfully')
    dialogVisible.value = false
    fetchConfigs()
  } catch (error) {
    ElMessage.error('Failed to save config')
  }
}

const deleteConfig = async (id) => {
  try {
    await axios.delete(`/api/v1/configs/${id}`)
    ElMessage.success('Deleted successfully')
    fetchConfigs()
  } catch (error) {
    ElMessage.error('Failed to delete config')
  }
}

onMounted(fetchConfigs)
</script>

<style scoped>
.config-view {
    padding: 20px;
}
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
</style>
