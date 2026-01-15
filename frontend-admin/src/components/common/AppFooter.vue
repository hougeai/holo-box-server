<template>
  <footer f-c-c flex-col text-14 color="#6a6a6a">
    © 2025-2030 {{ brandName }}, Inc. All rights reserved.
  </footer>
</template>

<script setup>
const brandName = import.meta.env.VITE_APP_BRAND_NAME || ''
</script>
