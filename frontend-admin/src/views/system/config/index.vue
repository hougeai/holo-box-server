<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NPopconfirm } from 'naive-ui'

import { formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'

import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '配置管理' })

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
  name: '配置',
  initForm: {},
  doCreate: api.createConfig,
  doUpdate: api.updateConfig,
  doDelete: api.deleteConfig,
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
    title: '配置键',
    key: 'key',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '配置值',
    key: 'value',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '备注',
    key: 'note',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '创建时间',
    key: 'create_at',
    align: 'center',
    width: 60,
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
    width: 60,
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
              onClick: () => handleEdit(row),
            },
            {
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            },
          ),
          [[vPermission, 'post/api/v1/base/config/update']],
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
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  },
                ),
                [[vPermission, 'delete/api/v1/base/config/delete']],
              ),
            default: () => h('div', {}, '确定删除该配置吗?'),
          },
        ),
      ]
    },
  },
]

const validateConfig = {
  key: [
    {
      required: true,
      message: '请输入配置键',
      trigger: ['input', 'blur'],
    },
  ],
  value: [
    {
      required: true,
      message: '请输入配置值',
      trigger: ['input', 'blur'],
    },
  ],
}
</script>

<template>
  <CommonPage show-footer title="配置管理">
    <template #action>
      <NButton v-permission="'post/api/v1/base/config/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建配置
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getConfigList"
    >
      <template #queryBar>
        <QueryBarItem label="配置键" :label-width="60">
          <NInput
            v-model:value="queryItems.key"
            clearable
            type="text"
            placeholder="请输入配置键"
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
        :rules="validateConfig"
      >
        <NFormItem label="配置键" path="key">
          <NInput v-model:value="modalForm.key" clearable placeholder="请输入配置键" />
        </NFormItem>
        <NFormItem label="配置值" path="value">
          <NInput
            v-model:value="modalForm.value"
            type="textarea"
            clearable
            placeholder="请输入配置值"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </NFormItem>
        <NFormItem label="备注" path="note">
          <NInput
            v-model:value="modalForm.note"
            type="textarea"
            clearable
            placeholder="请输入备注"
            :autosize="{ minRows: 2, maxRows: 4 }"
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
