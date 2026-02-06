<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NInput, NSwitch, NTag, NModal, NForm, NFormItem, NPopconfirm } from 'naive-ui'

import { formatDateTime, renderIcon } from '@/utils'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: '设备管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const userStore = useUserStore()

// 绑定设备对话框
const bindModalVisible = ref(false)
const bindFormRef = ref(null)
const bindForm = ref({
  user_id: '',
  agent_id: '',
  code: '',
})
const bindLoading = ref(false)

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '用户ID',
    key: 'user_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '智能体ID',
    key: 'agent_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '设备ID',
    key: 'device_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'MAC地址',
    key: 'mac_address',
    align: 'center',
    width: 30,
    ellipsis: { tooltip: true },
  },
  {
    title: '序列号',
    key: 'serial_number',
    align: 'center',
    width: 30,
    ellipsis: { tooltip: true },
  },
  {
    title: '芯片型号',
    key: 'chip_type',
    align: 'center',
    width: 30,
    ellipsis: { tooltip: true },
  },
  {
    title: '设备型号',
    key: 'device_model',
    align: 'center',
    width: 30,
    ellipsis: { tooltip: true },
  },
  {
    title: '软件版本',
    key: 'app_version',
    align: 'center',
    width: 30,
    ellipsis: { tooltip: true },
  },
  {
    title: 'OTA升级',
    key: 'auto_update',
    width: 30,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.auto_update,
        loading: !!row.publishing, // 将变量强制转换为布尔值
        checkedValue: true,
        uncheckedValue: false,
        onUpdateValue: () => handleUpdateOta(row),
      })
    },
  },
  {
    title: '最近对话',
    key: 'last_conversation',
    align: 'center',
    width: 40,
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () =>
            row.last_conversation !== null ? formatDateTime(row.last_conversation) : '-',
        },
      )
    },
  },
  {
    title: '创建时间',
    key: 'create_at',
    width: 40,
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
    title: '是否解绑过',
    key: 'is_unbound',
    width: 30,
    align: 'center',
    render(row) {
      return h(
        NTag,
        {
          size: 'small',
          type: row.is_unbound ? 'error' : 'success',
        },
        {
          default: () => (row.is_unbound ? '是' : '否'),
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
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleUnbind({ id: row.id }),
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
                    default: () => '解绑',
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  },
                ),
                [[vPermission, 'delete/api/v1/device/unbind']],
              ),
            default: () => h('div', {}, '确定解绑吗?'),
          },
        ),
      ]
    },
  },
]

// 修改OTA状态
async function handleUpdateOta(row) {
  if (!row.id) return
  row.publishing = true
  const newStatus = !row.auto_update
  try {
    await api.updateDevice({ id: row.id, auto_update: newStatus })
    row.auto_update = newStatus
    $message?.success(newStatus ? '已启用OTA升级' : '已禁用OTA升级')
    $table.value?.handleSearch()
  } catch (err) {
    console.log(err)
  } finally {
    row.publishing = false
  }
}

// 打开绑定设备对话框
function openCreateModal() {
  bindForm.value = {
    user_id: userStore.userId,
    agent_id: '',
    code: '',
  }
  bindModalVisible.value = true
}

// 绑定设备
async function handleBindDevice() {
  bindFormRef.value?.validate(async (errors) => {
    if (errors) return
    bindLoading.value = true
    try {
      await api.bindDevice(bindForm.value)
      $message?.success('绑定成功')
      bindModalVisible.value = false
      $table.value?.handleSearch()
    } catch (err) {
      console.log(err)
    } finally {
      bindLoading.value = false
    }
  })
}

// 解绑设备
async function handleUnbind({ id }) {
  try {
    await api.unbindDevice({ id })
    $message?.success('解绑成功')
    $table.value?.handleSearch()
  } catch (err) {
    console.log(err)
  }
}
</script>

<template>
  <CommonPage show-footer title="设备列表">
    <template #action>
      <NButton type="primary" @click="openCreateModal">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />绑定设备
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getDeviceList"
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
        <QueryBarItem label="MAC地址" :label-width="70">
          <NInput
            v-model:value="queryItems.mac_address"
            clearable
            type="text"
            placeholder="请输入芯片型号"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 绑定设备对话框 -->
    <NModal
      v-model:show="bindModalVisible"
      preset="card"
      title="绑定设备"
      :style="{ width: '500px' }"
    >
      <NForm ref="bindFormRef" :model="bindForm" label-placement="left" label-width="80">
        <NFormItem
          label="用户ID"
          path="user_id"
          :rule="{ required: true, message: '请输入用户ID' }"
        >
          <NInput v-model:value="bindForm.user_id" placeholder="请输入用户ID" />
        </NFormItem>
        <NFormItem label="智能体ID" path="agent_id">
          <NInput v-model:value="bindForm.agent_id" placeholder="请输入智能体ID" />
        </NFormItem>
        <NFormItem label="验证码" path="code" :rule="{ required: true, message: '请输入验证码' }">
          <NInput v-model:value="bindForm.code" placeholder="请输入设备验证码" />
        </NFormItem>
      </NForm>
      <template #footer>
        <div class="flex justify-end gap-4">
          <NButton @click="bindModalVisible = false">取消</NButton>
          <NButton type="primary" :loading="bindLoading" @click="handleBindDevice">确定</NButton>
        </div>
      </template>
    </NModal>
  </CommonPage>
</template>
