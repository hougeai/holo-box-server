<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NInput, NPopconfirm, NFormItem } from 'naive-ui'

import { formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: '系统提示词管理' })

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
  name: '系统提示词',
  initForm: {
    user_id: userStore.userId,
  },
  doCreate: api.createSysPrompt,
  doUpdate: api.updateSysPrompt,
  doDelete: api.deleteSysPrompt,
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
    title: '提示词名称',
    key: 'name',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '提示词内容',
    key: 'content',
    width: 60,
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
          [[vPermission, 'post/api/v1/agent/sys-prompt/update']],
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
                [[vPermission, 'delete/api/v1/agent/sys-prompt/delete']],
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
  <CommonPage show-footer title="系统提示词列表">
    <template #action>
      <NButton
        v-permission="'post/api/v1/agent/sys-prompt/create'"
        type="primary"
        @click="handleAdd"
      >
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新增系统提示词
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getSysPromptList"
    >
      <template #queryBar>
        <QueryBarItem label="系统提示词名称" :label-width="100">
          <NInput
            v-model:value="queryItems.agent_name"
            clearable
            type="text"
            placeholder="请输入系统提示词名称"
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
            message: '请输入系统提示词名称',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.name"
            placeholder="请输入系统提示词名称"
            maxlength="20"
            show-count
          />
        </NFormItem>
        <NFormItem
          label="内容"
          path="content"
          :rule="{
            required: true,
            message: '请输入系统提示词内容',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.content"
            type="textarea"
            :rows="8"
            clearable
            placeholder="请输入角色提示词"
            maxlength="990"
            show-count
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
