<script setup>
const props = defineProps({
  icon: {
    type: String,
    required: true,
  },
  prefix: {
    type: String,
    default: 'icon-custom',
  },
  color: {
    type: String,
    default: 'currentColor',
  },
})

const symbolId = computed(() => `#${props.prefix}-${props.icon}`)
</script>

<template>
  <!-- aria-hidden="true" 表示对屏幕阅读器隐藏 1em 使图标大小跟随字体大小 -->
  <svg aria-hidden="true" width="1em" height="1em">
    <use :xlink:href="symbolId" :fill="color" />
  </svg>
</template>
