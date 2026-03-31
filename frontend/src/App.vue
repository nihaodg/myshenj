<template>
  <div id="app">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1 class="logo">DeepAudit Lite</h1>
          <el-menu
            mode="horizontal"
            :default-active="activeMenu"
            router
            class="header-menu"
          >
            <el-menu-item index="/">仪表盘</el-menu-item>
            <el-menu-item index="/audit">审计任务</el-menu-item>
            <el-menu-item index="/monitor">实时监控</el-menu-item>
            <el-menu-item index="/topology">拓扑编辑</el-menu-item>
            <el-menu-item index="/rules">规则管理</el-menu-item>
            <el-menu-item index="/settings">系统设置</el-menu-item>
          </el-menu>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Microsoft YaHei', Arial, sans-serif;
}

#app {
  min-height: 100vh;
}

.el-header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.logo {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
  margin-right: 40px;
}

.header-menu {
  border-bottom: none;
}

.el-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
