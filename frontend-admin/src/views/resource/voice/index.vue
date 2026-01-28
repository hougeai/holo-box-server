<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NInput, NTag, NSelect, NSwitch } from 'naive-ui'

import { formatDateTime, languageMap } from '@/utils'
import api from '@/api'

defineOptions({ name: '音色管理' })

const $table = ref(null) // 只是说明这是一个特殊的实例
const queryItems = ref({
  user_id: null,
  voice_id: null,
  public: null,
  language: null,
})

// 是否公开选项
const publicOptions = [
  { label: '全部', value: null },
  { label: '是', value: true },
  { label: '否', value: false },
]

// 语言选项
const languageOptions = [
  { label: '全部', value: null },
  ...Object.entries(languageMap).map(([key, label]) => ({ label, value: key })),
]

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
    title: '是否公开',
    key: 'public',
    width: 30,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        value: row.public,
        onUpdateValue: async (value) => {
          try {
            const res = await api.updateVoice({
              id: row.id,
              public: value,
            })
            if (res.code === 200) {
              $message.success('更新成功')
              $table.value?.handleSearch()
            } else {
              $message.error(res.msg || '更新失败')
            }
          } catch (error) {
            console.error(error)
            $message.error('更新失败')
          }
        },
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
        <QueryBarItem label="用户ID" :label-width="60" :content-width="140">
          <NInput
            v-model:value="queryItems.user_id"
            clearable
            type="text"
            placeholder="请输入用户ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="音色ID" :label-width="60" :content-width="140">
          <NInput
            v-model:value="queryItems.voice_id"
            clearable
            type="text"
            placeholder="请输入音色ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="是否公开" :label-width="60" :content-width="140">
          <NSelect
            v-model:value="queryItems.public"
            :options="publicOptions"
            clearable
            placeholder="请选择"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="语言" :label-width="40" :content-width="140">
          <NSelect
            v-model:value="queryItems.language"
            :options="languageOptions"
            clearable
            placeholder="请选择"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
