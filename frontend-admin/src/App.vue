<template>
  <!-- 用于提供应用级的上下文/状态，作为所有路由组件的统一入口点，保持应用布局的一致性 -->
  <AppProvider>
    <!-- 获取当前路由对应的组件，动态渲染当前路由组件 -->
    <router-view v-slot="{ Component }">
      <component :is="Component" />
    </router-view>
  </AppProvider>
</template>

<script setup>
// 组件已自动导入，无需手动导入
// import AppProvider from '@/components/common/AppProvider.vue'
</script>
