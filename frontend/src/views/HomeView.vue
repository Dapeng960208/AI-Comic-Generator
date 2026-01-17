<template>
  <div class="home-view">
    <div class="header">
      <h2>My Projects</h2>
      <el-button type="primary" @click="dialogVisible = true">New Project</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="6" v-for="project in projects" :key="project.id">
        <el-card shadow="hover" class="project-card" @click="goToProject(project.id)">
          <template #header>
            <div class="card-header">
              <span>{{ project.title }}</span>
              <el-button type="text" icon="Delete" @click.stop="deleteProject(project.id)"></el-button>
            </div>
          </template>
          <p>{{ project.description || 'No description' }}</p>
          <div class="footer">
            <span>{{ new Date(project.updated_at).toLocaleDateString() }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" title="Create New Project">
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
        <el-button type="primary" @click="createProject">Create</el-button>
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
const form = ref({ title: '', description: '' })

const fetchProjects = async () => {
  try {
    const res = await axios.get('/api/v1/projects/')
    projects.value = res.data
  } catch (error) {
    ElMessage.error('Failed to fetch projects')
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
</style>
