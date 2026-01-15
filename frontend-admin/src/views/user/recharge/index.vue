<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NInput, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'

import CrudTable from '@/components/table/CrudTable.vue'

import { formatDateTime } from '@/utils'
import api from '@/api'

defineOptions({ name: '充值管理' })

const $table = ref(null)
const queryItems = ref({})

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  {
    title: '用户ID',
    key: 'user_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '订单ID',
    key: 'order_id',
    width: 80,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '支付方式',
    key: 'payment_method',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '金额',
    key: 'amount',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
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
  {
    title: '支付状态',
    key: 'is_paid',
    width: 40,
    align: 'center',
    render(row) {
      return h(
        NTag,
        {
          size: 'small',
          type: row.is_paid ? 'error' : 'success',
        },
        {
          default: () => (row.is_paid ? '已支付' : '待支付'),
        },
      )
    },
  },
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage show-footer title="充值列表">
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRechargeList"
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
        <QueryBarItem label="订单ID" :label-width="60">
          <NInput
            v-model:value="queryItems.order_id"
            clearable
            type="text"
            placeholder="请输入订单ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="是否支付" :label-width="60">
          <NSelect
            v-model:value="queryItems.is_paid"
            :options="[
              { label: '已支付', value: true },
              { label: '待支付', value: false },
            ]"
            clearable
            placeholder="请选择"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
