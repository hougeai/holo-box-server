<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NPopconfirm, NSwitch, NTag } from 'naive-ui'

import { formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'

import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '商品管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '商品',
  initForm: {},
  doCreate: api.createProduct,
  doUpdate: api.updateProduct,
  doDelete: api.deleteProduct,
  refresh: () => $table.value?.handleSearch(),
})

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
    title: '商品标识',
    key: 'key',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '商品名称',
    key: 'name',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '积分价格',
    key: 'points_price',
    width: 40,
    align: 'center',
  },
  {
    title: '商品描述',
    key: 'description',
    width: 80,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '状态',
    key: 'is_public',
    width: 40,
    align: 'center',
    render(row) {
      return h(
        NTag,
        { type: row.is_public ? 'success' : 'default', size: 'small' },
        { default: () => (row.is_public ? '上架' : '下架') },
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
  {
    title: '操作',
    key: 'actions',
    width: 80,
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
              onClick: () => handleEdit(row),
            },
            {
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            },
          ),
          [[vPermission, 'post/api/v1/finance/product/update']],
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
                    loading: modalLoading.value,
                  },
                  {
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  },
                ),
                [[vPermission, 'delete/api/v1/finance/product/delete']],
              ),
            default: () => h('div', {}, '确定删除该商品吗?'),
          },
        ),
      ]
    },
  },
]

const validateProduct = {
  key: [
    {
      required: true,
      message: '请输入商品标识',
      trigger: ['input', 'blur'],
    },
  ],
  name: [
    {
      required: true,
      message: '请输入商品名称',
      trigger: ['input', 'blur'],
    },
  ],
  points_price: [
    {
      required: true,
      message: '请输入积分价格',
      trigger: ['input', 'blur'],
      type: 'number',
      transform: (value) => Number(value),
    },
    {
      type: 'number',
      min: 0,
      message: '积分价格不能小于0',
      trigger: ['input', 'blur'],
      transform: (value) => Number(value),
    },
  ],
}
</script>

<template>
  <CommonPage show-footer title="商品管理">
    <template #action>
      <NButton
        v-permission="'post/api/v1/finance/product/create'"
        type="primary"
        @click="handleAdd"
      >
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建商品
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getProductList"
    >
      <template #queryBar>
        <QueryBarItem label="商品名称" :label-width="80">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入商品名称"
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
        :label-width="100"
        :model="modalForm"
        :rules="validateProduct"
      >
        <NFormItem label="商品标识" path="key">
          <NInput v-model:value="modalForm.key" clearable placeholder="请输入商品标识" />
        </NFormItem>
        <NFormItem label="商品名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入商品名称" />
        </NFormItem>
        <NFormItem label="积分价格" path="points_price">
          <NInputNumber
            v-model:value="modalForm.points_price"
            :min="0"
            :precision="0"
            placeholder="请输入积分价格"
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem label="商品描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            type="textarea"
            clearable
            placeholder="请输入商品描述"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </NFormItem>
        <NFormItem label="是否上架" path="is_public">
          <NSwitch v-model:value="modalForm.is_public"> </NSwitch>
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
