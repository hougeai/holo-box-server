<template>
  <n-layout has-sider wh-full>
    <!-- 左侧边栏 -->
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      :native-scrollbar="false"
      :collapsed="appStore.collapsed"
    >
      <SideBar />
    </n-layout-sider>
    <!-- 右侧主体内容 -->
    <!-- article是html5的语义化标签-对搜索引擎更好，表示独立完整的内容区域，也可以用div -->
    <article flex-col flex-1 overflow-hidden>
      <!-- 顶部导航栏 -->
      <header
        class="flex items-center border-b bg-white px-15 bc-eee"
        dark="bg-dark border-0"
        :style="`height: ${header.height}px`"
      >
        <AppHeader />
      </header>
      <!-- 标签页导航 -->
      <section v-if="tags.visible" hidden border-b bc-eee sm:block dark:border-0>
        <AppTags :style="{ height: `${tags.height}px` }" />
      </section>
      <!-- 主内容区域 -->
      <section flex-1 overflow-hidden bg-hex-f5f6fb dark:bg-hex-101014>
        <AppMain />
      </section>
    </article>
  </n-layout>
</template>

<script setup>
// 这些都是在layout文件夹下的组件，不是自动导入的
import AppHeader from './components/header/index.vue'
import SideBar from './components/sidebar/index.vue'
import AppMain from './components/AppMain.vue'
import AppTags from './components/tags/index.vue'
import { useAppStore } from '@/store'
import { header, tags } from '~/settings' // settings中定义了header tags的高度

// 移动端适配
import { useBreakpoints } from '@vueuse/core'

const appStore = useAppStore()
const breakpointsEnum = {
  xl: 1600,
  lg: 1199,
  md: 991,
  sm: 666,
  xs: 575,
}
const breakpoints = reactive(useBreakpoints(breakpointsEnum))
const isMobile = breakpoints.smaller('sm')
const isPad = breakpoints.between('sm', 'md')
const isPC = breakpoints.greater('md')
// Vue3 的响应式 API 监听屏幕尺寸变化
watchEffect(() => {
  if (isMobile.value) {
    // Mobile
    appStore.setCollapsed(true) // 收起侧边栏
    appStore.setFullScreen(false) // 不全屏显示
  }

  if (isPad.value) {
    // IPad
    appStore.setCollapsed(true)
    appStore.setFullScreen(false)
  }

  if (isPC.value) {
    // PC
    appStore.setCollapsed(false)
    appStore.setFullScreen(true)
  }
})
</script>
