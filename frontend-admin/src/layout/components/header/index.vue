<template>
  <div flex items-center>
    <MenuCollapse />
    <!-- 折叠菜单按钮 -->
    <BreadCrumb ml-15 hidden sm:block />
    <!-- 面包屑导航，小屏隐藏 -->
  </div>
  <div ml-auto flex items-center>
    <!-- ml-auto 使这个 div 靠右对齐 -->
    <Languages />
    <ThemeMode />
    <GithubSite />
    <FullScreen />
    <UserAvatar />
  </div>
</template>

<script setup>
import BreadCrumb from './components/BreadCrumb.vue'
import MenuCollapse from './components/MenuCollapse.vue'
import FullScreen from './components/FullScreen.vue'
import UserAvatar from './components/UserAvatar.vue'
import GithubSite from './components/GithubSite.vue'
import ThemeMode from './components/ThemeMode.vue'
import Languages from './components/Languages.vue'
</script>
