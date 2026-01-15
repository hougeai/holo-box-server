<script setup>
import { renderIcon } from '@/utils'

defineProps({
  icon: {
    type: String,
    required: true,
  },
  size: {
    type: Number,
    default: 14,
  },
  color: {
    type: String,
    default: undefined,
  },
})
</script>

<template>
  <!-- component 是 Vue 内置的特殊组件，用于动态渲染组件或 HTML 元素 :is 属性决定实际渲染的内容-->
  <component :is="renderIcon(icon, { size, color })" />
</template>
