<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NTag, NTooltip } from 'naive-ui'

import { formatDateTime } from '@/utils'

import api from '@/api'

defineOptions({ name: '积分流水' })

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
    title: '流水类型',
    key: 'flow_type',
    width: 40,
    align: 'center',
    render(row) {
      const typeMap = {
        recharge: { type: 'success', text: '充值' },
        gift: { type: 'info', text: '赠送' },
        order: { type: 'warning', text: '消费' },
        expire: { type: 'error', text: '过期' },
        refund: { type: 'error', text: '退款' },
      }
      const config = typeMap[row.flow_type] || { type: 'default', text: row.flow_type }
      return h(NTag, { type: config.type, size: 'small' }, { default: () => config.text })
    },
  },
  {
    title: '积分数额',
    key: 'amount',
    width: 40,
    align: 'center',
    render(row) {
      const isPositive = row.amount >= 0
      const type = isPositive ? 'success' : 'error'
      const text = `${isPositive ? '+' : ''}${row.amount}`
      return h(NTag, { type, size: 'small' }, { default: () => text })
    },
  },
  {
    title: '变动后余额',
    key: 'balance',
    width: 50,
    align: 'center',
    render(row) {
      return h(NTag, { type: 'default', size: 'small' }, { default: () => `${row.balance} 积分` })
    },
  },
  {
    title: '关联授予ID',
    key: 'grant_ids',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      if (!row.grant_ids || row.grant_ids.length === 0) {
        return h('span', {}, '-')
      }
      const ids = row.grant_ids.join(', ')
      return h(
        NTooltip,
        {},
        {
          trigger: () => h('span', {}, ids),
          default: () => ids,
        },
      )
    },
  },
  {
    title: '关联订单ID',
    key: 'order_id',
    width: 40,
    align: 'center',
    render(row) {
      if (!row.order_id) {
        return h('span', {}, '-')
      }
      return h(
        NTooltip,
        {},
        {
          trigger: () => h('span', {}, row.order_id),
          default: () => row.order_id,
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
  <CommonPage show-footer title="积分流水">
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getPointsFlowList"
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
        <QueryBarItem label="流水类型" :label-width="80">
          <NSelect
            v-model:value="queryItems.flow_type"
            clearable
            placeholder="请选择流水类型"
            :options="[
              { label: '充值', value: 'recharge' },
              { label: '赠送', value: 'gift' },
              { label: '消费', value: 'order' },
              { label: '过期', value: 'expire' },
              { label: '退款', value: 'refund' },
            ]"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
