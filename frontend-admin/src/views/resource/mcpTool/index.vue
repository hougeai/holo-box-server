<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NInput, NPopconfirm, NFormItem, NTag, NSwitch, NPopover } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { formatDateTime, renderIcon, formatJSON } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: 'MCP管理' })

const protocolOptions = [
  { label: 'sse', value: 'sse' },
  { label: 'StreamableHttp', value: 'http' },
]

// 将数组格式的环境变量转换为对象
function convertArrayToObject(arr) {
  if (!arr || !Array.isArray(arr) || arr.length === 0) return {}
  const obj = {}
  arr.forEach((item) => {
    if (item.key !== undefined && item.value !== undefined) {
      obj[item.key] = item.value
    }
  })
  return obj
}

// 将对象格式的环境变量转换为数组
function convertObjectToArray(obj) {
  if (!obj || typeof obj !== 'object') return []

  return Object.keys(obj).map((key) => ({
    key,
    value: obj[key],
  }))
}

// 数据预处理函数
function handleProcessData() {
  // 创建config对象
  if (modalForm.value.protocol === 'stdio') {
    // stdio协议
    modalForm.value.config = {
      command: modalForm.value.command,
      args: modalForm.value.args || [],
      env: convertArrayToObject(modalForm.value.env) || {},
    }
    // 删除临时字段
    delete modalForm.value.command
    delete modalForm.value.args
    delete modalForm.value.env
  } else {
    // http/sse协议
    modalForm.value.config = {
      url: modalForm.value.url,
      headers: convertArrayToObject(modalForm.value.headers) || {},
    }
    // 删除临时字段
    delete modalForm.value.url
    delete modalForm.value.args
  }
  return true
}

// 编辑时数据处理
function handleEditWithData(row) {
  handleEdit(row)
  // 将config中的数据提取到表单字段中
  if (row.config) {
    if (row.protocol === 'stdio') {
      // stdio协议处理
      modalForm.value.command = row.config.command || ''
      modalForm.value.args = Array.isArray(row.config.args) ? row.config.args : []
      modalForm.value.env = convertObjectToArray(row.config.env || {})
    } else {
      // http/sse协议处理
      modalForm.value.url = row.config.url || ''
      modalForm.value.headers = convertObjectToArray(row.config.headers || {})
    }
  }
}

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
    title: '协议',
    key: 'protocol',
    width: 20,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '配置',
    key: 'config',
    width: 20,
    align: 'center',
    ellipsis: { tooltip: true },
    render: (row) => {
      return h(
        NPopover,
        {
          trigger: 'hover',
          placement: 'right',
        },
        {
          trigger: () =>
            h('div', { style: 'cursor: pointer;' }, [h(TheIcon, { icon: 'carbon:data-view' })]),
          default: () =>
            h(
              'pre',
              {
                style:
                  'max-height: 400px; overflow: auto; background-color: #f5f5f5; padding: 8px; border-radius: 4px;',
              },
              formatJSON(row.config),
            ),
        },
      )
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
                handleEditWithData(row)
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
      @save="() => handleSave(handleProcessData)"
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
        <NFormItem label="协议" path="protocol">
          <NSelect
            v-model:value="modalForm.protocol"
            :options="protocolOptions"
            clearable
            placeholder="请选择MCP协议"
          />
        </NFormItem>
        <template v-if="['sse', 'http'].includes(modalForm.protocol)">
          <NFormItem label="服务地址" path="url">
            <NInput v-model:value="modalForm.url" clearable placeholder="请输入服务地址" />
          </NFormItem>

          <NFormItem label="Headers">
            <NDynamicInput
              v-model:value="modalForm.headers"
              preset="pair"
              key-placeholder="Header名称"
              value-placeholder="Header值"
            />
          </NFormItem>
        </template>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
