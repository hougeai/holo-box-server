<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NTag } from 'naive-ui'

import { formatDateTime } from '@/utils'

import api from '@/api'

defineOptions({ name: '积分授予' })

const $table = ref(null)
const queryItems = ref({})

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 20,
    align: 'center',
  },
  {
    title: '用户ID',
    key: 'user_id',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '剩余积分',
    key: 'amount',
    width: 40,
    align: 'center',
    render(row) {
      return h(
        NTag,
        { type: row.amount > 0 ? 'success' : 'default', size: 'small' },
        {
          default: () => `${row.amount} 积分`,
        },
      )
    },
  },
  {
    title: '来源类型',
    key: 'source_type',
    width: 40,
    align: 'center',
    render(row) {
      const typeMap = {
        recharge: { type: 'info', text: '充值' },
        gift: { type: 'warning', text: '赠送' },
      }
      const config = typeMap[row.source_type] || { type: 'default', text: row.source_type }
      return h(NTag, { type: config.type, size: 'small' }, { default: () => config.text })
    },
  },
  {
    title: '来源ID',
    key: 'source_id',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '过期时间',
    key: 'expired_at',
    width: 70,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () => (row.expired_at !== null ? formatDateTime(row.expired_at) : '永久有效'),
        },
      )
    },
  },
  {
    title: '创建时间',
    key: 'create_at',
    align: 'center',
    width: 70,
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
  {
    title: '更新时间',
    key: 'update_at',
    align: 'center',
    width: 70,
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () => (row.update_at !== null ? formatDateTime(row.update_at) : null),
        },
      )
    },
  },
]
</script>

<template>
  <CommonPage show-footer title="积分授予">
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getPointsGrantList"
    >
      <template #queryBar>
        <QueryBarItem label="用户ID" :label-width="80">
          <NInput
            v-model:value="queryItems.user_id"
            clearable
            type="text"
            placeholder="请输入用户ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="来源类型" :label-width="80">
          <NSelect
            v-model:value="queryItems.source_type"
            clearable
            placeholder="请选择来源类型"
            :options="[
              { label: '充值', value: 'recharge' },
              { label: '赠送', value: 'gift' },
            ]"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
