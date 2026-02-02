<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NInput, NPopconfirm, NFormItem, NTag, NSwitch } from 'naive-ui'

import { formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: 'MCP管理' })

const $table = ref(null) // 只是说明这是一个特殊的实例
const queryItems = ref({})
const vPermission = resolveDirective('permission') // 用来解析自定义指令，是app.directive('permission', {})定义的
const userStore = useUserStore()

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleAdd,
  handleDelete,
} = useCRUD({
  name: 'MCP工具',
  initForm: {
    user_id: userStore.userId,
  },
  doCreate: api.createMcpTool,
  doUpdate: api.updateMcpTool,
  doDelete: api.deleteMcpTool,
  refresh: () => $table.value?.handleSearch(), // 在CrudTable中定义的
})

onMounted(async () => {
  $table.value?.handleSearch()
})

const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 20,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'MCP端点ID',
    key: 'endpoint_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'MCP名称',
    key: 'name',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'MCP描述',
    key: 'description',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'MCP来源',
    key: 'source',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'Token',
    key: 'token',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '是否启用',
    key: 'enabled',
    width: 30,
    align: 'center',
    render(row) {
      return h(
        NTag,
        {
          size: 'small',
          type: row.enabled ? 'error' : 'success',
        },
        {
          default: () => (row.enabled ? '是' : '否'),
        },
      )
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
            const res = await api.updateMcpTool({
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
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            },
          ),
          [[vPermission, 'post/api/v1/agent/mcp-tool/update']],
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }),
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
                [[vPermission, 'delete/api/v1/agent/mcp-tool/delete']],
              ),
            default: () => h('div', {}, '确定删除吗?'),
          },
        ),
      ]
    },
  },
]
</script>

<template>
  <CommonPage show-footer title="MCP工具列表">
    <template #action>
      <NButton v-permission="'post/api/v1/agent/mcp-tool/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新增MCP工具
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getMcpToolList"
    >
      <template #queryBar>
        <QueryBarItem label="名称" :label-width="100">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
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
        :label-width="110"
        :model="modalForm"
      >
        <NFormItem
          label="名称"
          path="name"
          :rule="{
            required: true,
            message: '请输入名称',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.name"
            placeholder="请输入名称"
            maxlength="20"
            show-count
          />
        </NFormItem>
        <NFormItem
          label="描述"
          path="description"
          :rule="{
            required: true,
            message: '请输入描述',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.description"
            type="textarea"
            :rows="2"
            clearable
            placeholder="请输入描述"
            maxlength="100"
            show-count
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
