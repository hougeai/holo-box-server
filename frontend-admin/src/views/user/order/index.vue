<script setup>
import { h, onMounted, ref } from 'vue'
import { NTag } from 'naive-ui'

import { formatDateTime } from '@/utils'
import { useCRUD } from '@/composables'

import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '订单管理' })

const $table = ref(null)
const queryItems = ref({})
const productOptions = ref([])

const { modalVisible, modalTitle, modalLoading, handleSave, modalForm, modalFormRef, handleAdd } =
  useCRUD({
    name: '订单',
    initForm: {},
    doCreate: api.createOrder,
    refresh: () => $table.value?.handleSearch(),
  })

onMounted(async () => {
  $table.value?.handleSearch()
  // 获取商品列表
  const res = await api.getProductList({ page: 1, page_size: 9999, is_public: true })
  productOptions.value = res.data
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
    title: '商品ID',
    key: 'product_id',
    width: 40,
    align: 'center',
  },
  {
    title: '消耗积分',
    key: 'points',
    width: 40,
    align: 'center',
  },
  {
    title: '订单状态',
    key: 'status',
    width: 40,
    align: 'center',
    render(row) {
      const statusMap = {
        completed: { type: 'success', text: '已完成' },
        cancelled: { type: 'error', text: '已取消' },
      }
      const config = statusMap[row.status] || { type: 'default', text: row.status }
      return h(NTag, { type: config.type, size: 'small' }, { default: () => config.text })
    },
  },
  {
    title: '创建时间',
    key: 'create_at',
    align: 'center',
    width: 70,
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', {}, row.create_at !== null ? formatDateTime(row.create_at) : null)
    },
  },
  {
    title: '更新时间',
    key: 'update_at',
    align: 'center',
    width: 70,
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', {}, row.update_at !== null ? formatDateTime(row.update_at) : null)
    },
  },
]

const validateOrder = {
  user_id: [
    {
      required: true,
      message: '请输入用户ID',
      trigger: ['input', 'blur'],
    },
  ],
  product_id: [
    {
      required: true,
      message: '请选择商品',
      trigger: ['change', 'blur'],
      type: 'number',
      transform: (value) => Number(value),
    },
  ],
}
</script>

<template>
  <CommonPage show-footer title="订单管理">
    <template #action>
      <NButton v-permission="'post/api/v1/finance/orders'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建订单
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getOrderList"
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
        <QueryBarItem label="订单状态" :label-width="80">
          <NSelect
            v-model:value="queryItems.status"
            clearable
            placeholder="请选择订单状态"
            :options="[
              { label: '已完成', value: 'completed' },
              { label: '已取消', value: 'cancelled' },
            ]"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
    <!-- 新建订单 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="100"
        :model="modalForm"
        :rules="validateOrder"
      >
        <NFormItem label="用户ID" path="user_id">
          <NInput v-model:value="modalForm.user_id" clearable placeholder="请输入用户ID" />
        </NFormItem>
        <NFormItem label="选择商品" path="product_id">
          <NSelect
            v-model:value="modalForm.product_id"
            clearable
            placeholder="请选择商品"
            :options="
              productOptions.map((p) => ({
                label: `${p.name} (${p.points_price}积分)`,
                value: p.id,
              }))
            "
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
