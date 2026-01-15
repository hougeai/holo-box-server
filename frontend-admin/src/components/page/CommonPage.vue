<template>
  <AppPage :show-footer="showFooter">
    <header v-if="showHeader" mb-15 min-h-45 flex items-center justify-between px-15>
      <!-- $slots 是 Vue 提供的内置属性，用于检查插槽是否被使用，当父组件有 "header"， $slots.header 就会存在 -->
      <slot v-if="$slots.header" name="header" />
      <template v-else>
        <h2 text-22 font-normal text-hex-333 dark:text-hex-ccc>{{ title || route.meta?.title }}</h2>
        <slot name="action" />
      </template>
    </header>

    <n-card flex-1 rounded-10>
      <slot />
    </n-card>
  </AppPage>
</template>

<script setup>
// 父组件会传递进来
defineProps({
  showFooter: {
    type: Boolean,
    default: true,
  },
  showHeader: {
    type: Boolean,
    default: true,
  },
  title: {
    type: String,
    default: undefined,
  },
})
const route = useRoute()
</script>
