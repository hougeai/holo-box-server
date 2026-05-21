<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NInput, NPopconfirm, NFormItem, NTag, NSwitch, NSelect, NInputNumber } from 'naive-ui'
import { formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: '闹钟管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
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
  name: '闹钟',
  initForm: {
    user_id: userStore.userId,
    alarm_type: 'once',
    delay_seconds: 0,
    cron_expr: '',
  },
  doCreate: api.createAlarm,
  doUpdate: api.updateAlarm,
  doDelete: api.deleteAlarm,
  refresh: () => $table.value?.handleSearch(),
})

onMounted(async () => {
  $table.value?.handleSearch()
})

const typeMap = {
  once: { label: '一次性', type: 'info' },
  recurring: { label: '周期性', type: 'success' },
}

const statusMap = {
  active: { label: '活跃', type: 'success' },
  disabled: { label: '禁用', type: 'warning' },
  triggered: { label: '已触发', type: 'info' },
  expired: { label: '已过期', type: 'error' },
}

const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 20,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '设备序列号',
    key: 'serial_number',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '提醒内容',
    key: 'name',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '类型',
    key: 'alarm_type',
    width: 20,
    align: 'center',
    render(row) {
      const item = typeMap[row.alarm_type] || { label: row.alarm_type, type: 'default' }
      return h(NTag, { size: 'small', type: item.type }, { default: () => item.label })
    },
  },
  {
    title: '延迟/周期',
    key: 'schedule',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      if (row.alarm_type === 'once') {
        return `${row.delay_seconds}秒`
      }
      return row.cron_expr || '-'
    },
  },
  {
    title: '下次触发',
    key: 'next_trigger_time',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return row.next_trigger_time ? formatDateTime(row.next_trigger_time) : '-'
    },
  },
  {
    title: '状态',
    key: 'status',
    width: 20,
    align: 'center',
    render(row) {
      const item = statusMap[row.status] || { label: row.status, type: 'default' }
      return h(NTag, { size: 'small', type: item.type }, { default: () => item.label })
    },
  },
  {
    title: '触发次数',
    key: 'trigger_count',
    width: 20,
    align: 'center',
  },
  {
    title: '上次触发',
    key: 'last_triggered',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return row.last_triggered ? formatDateTime(row.last_triggered) : '-'
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
        { default: () => (row.create_at !== null ? formatDateTime(row.create_at) : null) },
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
            { icon: renderIcon('material-symbols:edit', { size: 16 }) },
          ),
          [[vPermission, 'post/api/v1/agent/alarm/update']],
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
                  { size: 'small', type: 'error', style: 'margin-right: 8px;' },
                  { icon: renderIcon('material-symbols:delete-outline', { size: 16 }) },
                ),
                [[vPermission, 'delete/api/v1/agent/alarm/delete']],
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
  <CommonPage show-footer title="闹钟列表">
    <template #action>
      <NButton v-permission="'post/api/v1/agent/alarm/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新增闹钟
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getAlarmList"
    >
      <template #queryBar>
        <QueryBarItem label="设备序列号" :label-width="100">
          <NInput
            v-model:value="queryItems.serial_number"
            clearable
            type="text"
            placeholder="请输入设备序列号"
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
          label="设备序列号"
          path="serial_number"
          :rule="{
            required: true,
            message: '请输入设备序列号',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.serial_number"
            placeholder="请输入设备序列号"
            maxlength="64"
            show-count
          />
        </NFormItem>
        <NFormItem
          label="提醒内容"
          path="name"
          :rule="{
            required: true,
            message: '请输入提醒内容',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.name"
            placeholder="请输入提醒内容"
            maxlength="200"
            show-count
          />
        </NFormItem>
        <NFormItem label="闹钟类型" path="alarm_type">
          <NSelect
            v-model:value="modalForm.alarm_type"
            :options="[
              { label: '一次性', value: 'once' },
              { label: '周期性', value: 'recurring' },
            ]"
            placeholder="请选择闹钟类型"
          />
        </NFormItem>
        <NFormItem
          v-if="modalForm.alarm_type === 'once'"
          label="延迟秒数"
          path="delay_seconds"
          :rule="{
            type: 'number',
            min: 1,
            message: '请输入大于0的秒数',
            trigger: ['input', 'blur'],
          }"
        >
          <NInputNumber v-model:value="modalForm.delay_seconds" :min="1" placeholder="多少秒后触发" />
        </NFormItem>
        <NFormItem
          v-if="modalForm.alarm_type === 'recurring'"
          label="Cron表达式"
          path="cron_expr"
          :rule="{
            required: true,
            message: '请输入cron表达式',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.cron_expr"
            placeholder="例如: 0 9 * * *"
            maxlength="100"
            show-count
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
