<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NInput, NTag } from 'naive-ui'

import { formatDateTime, languageMap } from '@/utils'
import api from '@/api'

defineOptions({ name: '音色管理' })

const $table = ref(null) // 只是说明这是一个特殊的实例
const queryItems = ref({})

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  {
    title: '用户ID',
    key: 'user_id',
    width: 20,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '音色ID',
    key: 'voice_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '音色名称',
    key: 'voice_name',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '语言',
    key: 'language',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NTag,
        { type: 'info', style: { margin: '2px 3px' } },
        { default: () => languageMap[row.language] || '未知' },
      )
    },
  },
  {
    title: '音色预览',
    key: 'voice_demo',
    width: 40,
    align: 'center',
    render(row) {
      return h('audio', {
        controls: true,
        style: {
          width: '180px',
          height: '30px',
        },
        src: row.voice_demo,
      })
    },
  },
  {
    title: '创建时间',
    key: 'create_at',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () => (row.create_at !== null ? formatDateTime(row.create_at) : null),
        },
      )
    },
  },
]
</script>

<template>
  <CommonPage show-footer title="音色列表">
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getVoiceList"
    >
      <template #queryBar>
        <QueryBarItem label="用户ID" :label-width="60">
          <NInput
            v-model:value="queryItems.user_id"
            clearable
            type="text"
            placeholder="请输入用户ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="音色ID" :label-width="60">
          <NInput
            v-model:value="queryItems.voice_id"
            clearable
            type="text"
            placeholder="请输入音色ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
