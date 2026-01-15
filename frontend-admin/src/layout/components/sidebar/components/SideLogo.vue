<template>
  <router-link h-60 f-c-c to="/">
    <icon-custom-logo w-30 h-30 color-primary></icon-custom-logo>
    <h2
      v-show="!appStore.collapsed"
      ml-2
      mr-6
      max-w-150
      flex-shrink-0
      text-16
      font-bold
      color-primary
    >
      {{ title }}
    </h2>
  </router-link>
</template>

<script setup>
import { useAppStore } from '@/store'
const title = import.meta.env.VITE_TITLE

const appStore = useAppStore()
</script>
