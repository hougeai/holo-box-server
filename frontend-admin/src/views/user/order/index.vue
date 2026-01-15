<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NPopconfirm, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import { renderIcon, formatDateTime } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '订单管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const { modalVisible, modalTitle, modalLoading, handleSave, modalForm, handleEdit, handleDelete } =
  useCRUD({
    name: '订单管理',
    initForm: {},
    doCreate: api.createOrder,
    doUpdate: api.updateOrder,
    doDelete: api.deleteOrder,
    refresh: () => $table.value?.handleSearch(),
  })

onMounted(() => {
  $table.value?.handleSearch()
})

const editRules = {
  payment_period: [
    {
      required: true,
      message: '请输入payment_period',
      trigger: ['input', 'blur', 'change'],
    },
  ],
}

const columns = [
  {
    title: '用户ID',
    key: 'user_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '会员ID',
    key: 'role_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '支付周期',
    key: 'payment_period',
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
    title: '过期时间',
    key: 'expire_at',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () => (row.expire_at !== null ? formatDateTime(row.expire_at) : null),
        },
      )
    },
  },
  {
    title: '是否过期',
    key: 'is_expired',
    width: 40,
    align: 'center',
    render(row) {
      return h(
        NTag,
        {
          size: 'small',
          type: row.is_expired ? 'error' : 'success',
        },
        {
          default: () => (row.is_expired ? '是' : '否'),
        },
      )
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 60,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-right: 8px;',
              onClick: () => {
                handleEdit(row)
              },
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            },
          ),
          [[vPermission, 'post/api/v1/order/update']],
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }, false),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'error',
                    style: 'margin-right: 8px;',
                  },
                  {
                    default: () => '删除',
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  },
                ),
                [[vPermission, 'delete/api/v1/order/delete']],
              ),
            default: () => h('div', {}, '确定删除该订单记录吗?'),
          },
        ),
      ]
    },
  },
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage show-footer title="订单列表">
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getOrderList"
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
        <QueryBarItem label="会员ID" :label-width="60">
          <NInput
            v-model:value="queryItems.role_id"
            clearable
            type="text"
            placeholder="请输入会员ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑 弹窗 -->
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
        :label-width="80"
        :model="modalForm"
        :rules="editRules"
      >
        <NFormItem label="支付周期" path="payment_period">
          <NInput v-model:value="modalForm.payment_period" clearable placeholder="请输入API路径" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
