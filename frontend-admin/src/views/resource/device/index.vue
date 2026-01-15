<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NInput, NSwitch, NTag, NPopover } from 'naive-ui'

import TheIcon from '@/components/icon/TheIcon.vue'
import { formatDateTime, renderIcon, formatJSON } from '@/utils'
import api from '@/api'

defineOptions({ name: '设备管理' })

const $table = ref(null) // 只是说明这是一个特殊的实例
const queryItems = ref({})

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  {
    title: '设备ID',
    key: 'device_id',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '用户ID',
    key: 'user_id',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '设备位置',
    key: 'location',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '芯片型号',
    key: 'chip_type',
    align: 'center',
    width: 40,
    ellipsis: { tooltip: true },
  },
  {
    title: '模组型号',
    key: 'device_model',
    align: 'center',
    width: 60,
    ellipsis: { tooltip: true },
  },
  {
    title: '软件版本',
    key: 'app_version',
    align: 'center',
    width: 40,
    ellipsis: { tooltip: true },
  },
  {
    title: 'OTA升级',
    key: 'ota_enabled',
    width: 40,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.ota_enabled,
        loading: !!row.publishing, // 将变量强制转换为布尔值
        checkedValue: true,
        uncheckedValue: false,
        onUpdateValue: () => handleUpdateOta(row),
      })
    },
  },
  {
    title: '最近对话时间',
    key: 'last_conversation',
    align: 'center',
    width: 80,
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () =>
            row.last_conversation !== null ? formatDateTime(row.last_conversation) : null,
          icon: renderIcon('mdi:update', { size: 16 }),
        },
      )
    },
  },
  {
    title: '屏幕配置',
    key: 'display_setting',
    align: 'center',
    width: 80,
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
              formatJSON(row.display_setting),
            ),
        },
      )
    },
  },
  {
    title: '是否解绑过',
    key: 'is_unbound',
    width: 80,
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
]

// 修改OTA状态
async function handleUpdateOta(row) {
  if (!row.id) return
  row.publishing = true
  row.ota_enabled = !row.ota_enabled
  row.publishing = false
  try {
    await api.updateDevice(row)
    $message?.success(row.ota_enabled ? '已启用OTA升级' : '已禁用OTA升级')
    $table.value?.handleSearch()
  } catch (err) {
    // 有异常恢复原来的状态
    console.log(err)
    row.ota_enabled = !row.ota_enabled
  } finally {
    row.publishing = false
  }
}
</script>

<template>
  <CommonPage show-footer title="设备列表">
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getDeviceList"
    >
      <template #queryBar>
        <QueryBarItem label="设备ID" :label-width="60">
          <NInput
            v-model:value="queryItems.device_id"
            clearable
            type="text"
            placeholder="请输入设备ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="用户ID" :label-width="60">
          <NInput
            v-model:value="queryItems.user_id"
            clearable
            type="text"
            placeholder="请输入用户ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="芯片型号" :label-width="60">
          <NInput
            v-model:value="queryItems.chipType"
            clearable
            type="text"
            placeholder="请输入芯片型号"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
