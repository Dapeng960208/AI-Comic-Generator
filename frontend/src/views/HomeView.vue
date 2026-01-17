<template>
  <div class="home-view">
    <div class="header">
      <h2>My Projects</h2>
      <el-button type="primary" @click="openCreateDialog">New Project</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="6" v-for="project in projects" :key="project.id">
        <el-card shadow="hover" class="project-card" @click="goToProject(project.id)">
          <template #header>
            <div class="card-header">
              <span class="project-title" :title="project.title">{{ project.title }}</span>
              <div class="actions">
                <el-button type="text" icon="Edit" @click.stop="openEditDialog(project)"></el-button>
                <el-button type="text" icon="Delete" @click.stop="deleteProject(project.id)"></el-button>
              </div>
            </div>
          </template>
          <p class="project-desc">{{ project.description || 'No description' }}</p>
          <div class="footer">
            <span>{{ new Date(project.updated_at).toLocaleDateString() }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="isEdit ? 'Edit Project' : 'Create New Project'">
      <el-form :model="form">
        <el-form-item label="Title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input type="textarea" v-model="form.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="saveProject">{{ isEdit ? 'Save' : 'Create' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const projects = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({ id: '', title: '', description: '' })

const fetchProjects = async () => {
  try {
    const res = await axios.get('/api/v1/projects/')
    projects.value = res.data
  } catch (error) {
    ElMessage.error('Failed to fetch projects')
  }
}

const openCreateDialog = () => {
    isEdit.value = false
    form.value = { title: '', description: '' }
    dialogVisible.value = true
}

const openEditDialog = (project) => {
    isEdit.value = true
    form.value = { id: project.id, title: project.title, description: project.description }
    dialogVisible.value = true
}

const saveProject = async () => {
    if (isEdit.value) {
        await updateProject()
    } else {
        await createProject()
    }
}

const createProject = async () => {
  try {
    const res = await axios.post('/api/v1/projects/', form.value)
    ElMessage.success('Created successfully')
    dialogVisible.value = false
    goToProject(res.data.id)
  } catch (error) {
    ElMessage.error('Failed to create project')
  }
}

const updateProject = async () => {
  try {
    await axios.put(`/api/v1/projects/${form.value.id}`, {
        title: form.value.title,
        description: form.value.description
    })
    ElMessage.success('Updated successfully')
    dialogVisible.value = false
    fetchProjects()
  } catch (error) {
    ElMessage.error('Failed to update project')
  }
}

const deleteProject = async (id) => {
  try {
    await axios.delete(`/api/v1/projects/${id}`)
    ElMessage.success('Deleted successfully')
    fetchProjects()
  } catch (error) {
    ElMessage.error('Failed to delete project')
  }
}

const goToProject = (id) => {
  router.push(`/project/${id}`)
}

onMounted(fetchProjects)
</script>

<style scoped>
.home-view {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.project-card {
  cursor: pointer;
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.project-title {
    font-weight: bold;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 60%;
    display: inline-block;
}
.actions {
    display: flex;
    gap: 4px;
}
.project-desc {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    height: 3em;
    color: #666;
    font-size: 0.9em;
}
</style>
