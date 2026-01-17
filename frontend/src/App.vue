<template>
  <el-config-provider :locale="locale">
    <el-container>
      <el-header class="main-header">
        <div class="logo">AI Comic Generator</div>
        <el-menu mode="horizontal" router :default-active="$route.path" class="nav-menu">
          <el-menu-item index="/">Projects</el-menu-item>
          <el-menu-item index="/config">Models</el-menu-item>
        </el-menu>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-config-provider>
</template>

<script setup>
import { ref } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const locale = ref(zhCn)
</script>

<style scoped>
.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #333;
  background-color: #1e1e1e;
}
.logo {
  font-size: 1.5rem;
  font-weight: bold;
  color: #409EFF;
}
.nav-menu {
  border-bottom: none;
  background-color: transparent;
  width: 300px;
}
</style>
