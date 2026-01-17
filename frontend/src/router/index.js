import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ConfigView from '../views/ConfigView.vue'
import ProjectView from '../views/ProjectView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/config',
      name: 'config',
      component: ConfigView
    },
    {
      path: '/project/:id',
      name: 'project',
      component: ProjectView
    }
  ]
})

export default router
