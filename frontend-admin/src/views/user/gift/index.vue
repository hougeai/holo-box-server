<script setup>
import { h, onMounted, ref, resolveDirective } from 'vue'
import { NButton, NTag, NRadioGroup, NRadio } from 'naive-ui'

import { formatDateTime } from '@/utils'
import { useCRUD } from '@/composables'

import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '赠送管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const { modalVisible, modalTitle, modalLoading, handleSave, modalForm, modalFormRef, handleAdd } =
  useCRUD({
    name: '赠送',
    initForm: {
      user_id: '',
      points: null,
      gift_type: 'register',
      note: '',
      expired_at: null,
    },
    doCreate: api.createGift,
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
    title: '用户ID',
    key: 'user_id',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '赠送积分',
    key: 'points',
    width: 40,
    align: 'center',
  },
  {
    title: '赠送类型',
    key: 'gift_type',
    width: 40,
    align: 'center',
    render(row) {
      const typeMap = {
        register: { type: 'success', text: '注册赠送' },
        activity: { type: 'info', text: '活动赠送' },
        compensation: { type: 'warning', text: '补偿赠送' },
      }
      const config = typeMap[row.gift_type] || { type: 'default', text: row.gift_type }
      return h(NTag, { type: config.type, size: 'small' }, { default: () => config.text })
    },
  },
  {
    title: '备注',
    key: 'note',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '过期时间',
    key: 'expired_at',
    width: 70,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () => (row.expired_at !== null ? formatDateTime(row.expired_at) : '永久有效'),
        },
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
]

const validateGift = {
  user_id: [
    {
      required: true,
      message: '请输入用户ID',
      trigger: ['input', 'blur'],
    },
  ],
  points: [
    {
      required: true,
      message: '请输入赠送积分',
      trigger: ['input', 'blur'],
      type: 'number',
      transform: (value) => Number(value),
    },
    {
      type: 'number',
      min: 1,
      message: '赠送积分不能小于1',
      trigger: ['input', 'blur'],
      transform: (value) => Number(value),
    },
  ],
  gift_type: [
    {
      required: true,
      message: '请选择赠送类型',
      trigger: ['change', 'blur'],
    },
  ],
}
</script>

<template>
  <CommonPage show-footer title="赠送管理">
    <template #action>
      <NButton v-permission="'post/api/v1/finance/gifts'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建赠送
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getGiftList"
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
        <QueryBarItem label="赠送类型" :label-width="80">
          <NSelect
            v-model:value="queryItems.gift_type"
            clearable
            placeholder="请选择赠送类型"
            :options="[
              { label: '注册赠送', value: 'register' },
              { label: '活动赠送', value: 'activity' },
              { label: '补偿赠送', value: 'compensation' },
            ]"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
    <!-- 新建赠送 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      :show-save="true"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="100"
        :model="modalForm"
        :rules="validateGift"
      >
        <NFormItem label="用户ID" path="user_id">
          <NInput v-model:value="modalForm.user_id" clearable placeholder="请输入用户ID" />
        </NFormItem>
        <NFormItem label="赠送积分" path="points">
          <NInputNumber
            v-model:value="modalForm.points"
            :min="1"
            :precision="0"
            placeholder="请输入赠送积分"
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem label="赠送类型" path="gift_type">
          <NRadioGroup v-model:value="modalForm.gift_type">
            <NRadio value="register">注册赠送</NRadio>
            <NRadio value="activity">活动赠送</NRadio>
            <NRadio value="compensation">补偿赠送</NRadio>
          </NRadioGroup>
        </NFormItem>
        <NFormItem label="备注" path="note">
          <NInput
            v-model:value="modalForm.note"
            type="textarea"
            clearable
            placeholder="请输入备注"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </NFormItem>
        <NFormItem label="过期时间" path="expired_at">
          <NDatePicker
            v-model:value="modalForm.expired_at"
            type="datetime"
            clearable
            placeholder="请选择过期时间（不选择则永久有效）"
            style="width: 100%"
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
