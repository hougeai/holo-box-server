<script setup>
import { h, onMounted, ref, resolveDirective } from 'vue'
import {
  NTag,
  NTooltip,
  NRadioGroup,
  NRadio,
  NAlert,
  NDescriptions,
  NDescriptionsItem,
  NButton,
  NModal,
  NFormItem,
  NInputNumber,
  NForm,
} from 'naive-ui'
import QRCode from 'qrcode.vue'

import { formatDateTime } from '@/utils'
import { useCRUD } from '@/composables'

import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '充值记录' })

const $table = ref(null)
const queryItems = ref({})
const step = ref(1)
const qrCodeUrl = ref('')
const paymentCompleted = ref(false)
const isPolling = ref(false)
const pollTimer = ref(null)
const pollCount = ref(0)
const MAX_POLL_COUNT = 10 // 最大轮询次数，每次5秒
const vPermission = resolveDirective('permission')

// 退款弹窗相关
const refundModalVisible = ref(false)
const refundModalLoading = ref(false)
const refundFormRef = ref(null)
const refundForm = ref({
  trade_id: '',
  amount: null,
  reason: '',
})
const currentRechargeRow = ref(null)

// 刷新按钮loading状态
const refreshingRowId = ref(null)

const { modalVisible, modalTitle, modalLoading, modalForm, modalFormRef, handleAdd } = useCRUD({
  name: '充值',
  initForm: {
    user_id: '',
    amount: null,
    payment_method: 'wechat',
    trade_id: '',
    points: 0,
  },
  doCreate: (data) => {
    // 覆盖默认的 handleSave，实现自定义的支付流程
    return api.createRecharge(data)
  },
  refresh: () => $table.value?.handleSearch(),
})

const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 20,
    align: 'center',
    render: (row) => h(NTooltip, {}, { trigger: () => row.id, default: () => row.id }),
  },
  {
    title: '用户ID',
    key: 'user_id',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '充值金额',
    key: 'amount',
    width: 30,
    align: 'center',
    render: (row) => `¥${row.amount}`,
  },
  {
    title: '获得积分',
    key: 'points',
    width: 30,
    align: 'center',
  },
  {
    title: '支付方式',
    key: 'payment_method',
    width: 30,
    align: 'center',
    render: (row) => {
      const config =
        row.payment_method === 'alipay'
          ? { type: 'info', text: '支付宝' }
          : { type: 'success', text: '微信' }
      return h(NTag, { type: config.type, size: 'small' }, { default: () => config.text })
    },
  },
  {
    title: '订单号',
    key: 'trade_id',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '支付状态',
    key: 'is_paid',
    width: 30,
    align: 'center',
    render: (row) =>
      h(
        NTag,
        { type: row.is_paid ? 'success' : 'warning', size: 'small' },
        { default: () => (row.is_paid ? '已支付' : '未支付') },
      ),
  },
  {
    title: '退款状态',
    key: 'is_refunded',
    width: 30,
    align: 'center',
    render: (row) =>
      row.is_refunded
        ? h(NTag, { type: 'error', size: 'small' }, { default: () => '已退款' })
        : row.is_paid
          ? h(NTag, { type: 'info', size: 'small' }, { default: () => '未退款' })
          : null,
  },
  {
    title: '退款金额',
    key: 'refund_amount',
    width: 30,
    align: 'center',
    render: (row) => (row.refund_amount ? `¥${row.refund_amount}` : '-'),
  },
  {
    title: '退款号',
    key: 'refund_id',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '创建时间',
    key: 'create_at',
    align: 'center',
    width: 40,
    ellipsis: { tooltip: true },
    render: (row) => h('span', {}, row.create_at !== null ? formatDateTime(row.create_at) : null),
  },
  {
    title: '更新时间',
    key: 'update_at',
    align: 'center',
    width: 40,
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', {}, row.update_at !== null ? formatDateTime(row.update_at) : null)
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
          NButton,
          {
            size: 'small',
            type: 'warning',
            style: 'margin-right: 8px;',
            disabled: !row.is_paid || row.refund_amount > 0,
            onClick: () => handleOpenRefund(row),
          },
          { default: () => '退款' },
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            loading: refreshingRowId.value === row.id,
            onClick: () => handleRefresh(row),
          },
          { default: () => '刷新' },
        ),
      ]
    },
  },
]

const validateRecharge = {
  user_id: [
    {
      required: true,
      message: '请输入用户ID',
      trigger: ['input', 'blur'],
    },
  ],
  amount: [
    {
      required: true,
      message: '请输入充值金额',
      trigger: ['input', 'blur'],
      type: 'number',
      transform: (value) => Number(value),
    },
    {
      type: 'number',
      min: 0.01,
      message: '充值金额不能小于0.01元',
      trigger: ['input', 'blur'],
      transform: (value) => Number(value),
    },
  ],
  payment_method: [
    {
      required: true,
      message: '请选择支付方式',
      trigger: ['change', 'blur'],
    },
  ],
}

// 退款表单验证
const validateRefund = {
  amount: [
    {
      required: true,
      message: '请输入退款金额',
      trigger: ['input', 'blur'],
      type: 'number',
      transform: (value) => Number(value),
    },
    {
      type: 'number',
      min: 0.01,
      message: '退款金额不能小于0.01元',
      trigger: ['input', 'blur'],
      transform: (value) => Number(value),
    },
  ],
}

// 打开退款弹窗
const handleOpenRefund = (row) => {
  currentRechargeRow.value = row
  refundForm.value = {
    trade_id: row.trade_id,
    amount: row.amount, // 默认为订单金额
    reason: '',
  }
  refundModalVisible.value = true
}

// 提交退款
const handleRefundSubmit = async () => {
  try {
    await refundFormRef.value?.validate()
    refundModalLoading.value = true

    // 调用退款接口
    const res = await api.createRefund({
      trade_id: refundForm.value.trade_id,
      amount: refundForm.value.amount,
      reason: refundForm.value.reason,
    })

    if (res.code === 200) {
      $message.success('退款成功')
      refundModalVisible.value = false
      $table.value?.handleSearch()
    } else {
      $message.error(res.msg || '退款失败')
    }
  } catch (error) {
    console.error('退款失败:', error)
  } finally {
    refundModalLoading.value = false
  }
}

// 刷新支付状态
const handleRefresh = async (row) => {
  try {
    refreshingRowId.value = row.id
    const res = await api.getRechargeStatus({ trade_id: row.trade_id })
    if (res.code === 200) {
      $message.success(res.data.is_paid ? '支付成功' : '支付状态已更新')
      $table.value?.handleSearch()
    } else {
      $message.error(res.msg || '查询失败')
    }
  } catch (error) {
    console.error('刷新支付状态失败:', error)
  } finally {
    refreshingRowId.value = null
  }
}

// 覆盖 handleSave 实现自定义支付流程
const handlePayment = async () => {
  try {
    await modalFormRef.value?.validate()
    modalLoading.value = true

    const res = await api.createRecharge({
      user_id: modalForm.value.user_id,
      amount: modalForm.value.amount,
      payment_method: modalForm.value.payment_method,
    })

    if (res.code === 200) {
      modalForm.value.trade_id = res.data.trade_id
      modalForm.value.points = res.data.points
      qrCodeUrl.value = res.data.qr_code
      step.value = 2
    } else {
      $message.error(res.msg || '创建充值订单失败')
    }
  } catch (error) {
    console.error('创建充值订单失败:', error)
  } finally {
    modalLoading.value = false
  }
}

const checkPaymentStatus = async () => {
  // 如果已经在轮询中，不允许重复点击
  if (isPolling.value) {
    return
  }

  isPolling.value = true
  startPolling()
}

const startPolling = () => {
  pollCount.value = 0
  pollTimer.value = setInterval(async () => {
    pollCount.value++

    try {
      const res = await api.getRechargeStatus({ trade_id: modalForm.value.trade_id })
      if (res.code === 200 && res.data.is_paid) {
        // 支付成功
        stopPolling()
        $message.success('支付成功！')
        modalVisible.value = false
        $table.value?.handleSearch()
      } else if (pollCount.value >= MAX_POLL_COUNT) {
        // 轮询超时
        stopPolling()
        isPolling.value = false
        $message.warning('查询超时，请稍后前往账单明细查看')
        modalVisible.value = false
      }
      // 如果未支付且未超时，继续轮询
    } catch (error) {
      console.error('轮询支付状态失败:', error)
      stopPolling()
      isPolling.value = false
    }
  }, 5000) // 每5秒轮询一次
}

const stopPolling = () => {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

// 重置表单时重置步骤
const originalHandleAdd = handleAdd
const handleAddWrapper = () => {
  step.value = 1
  qrCodeUrl.value = ''
  paymentCompleted.value = false
  isPolling.value = false
  pollCount.value = 0
  originalHandleAdd()
}

// 组件卸载时清理定时器
import { onUnmounted } from 'vue'
onUnmounted(() => {
  stopPolling()
})

onMounted(() => {
  $table.value?.handleSearch()
})
</script>

<template>
  <CommonPage show-footer title="充值记录">
    <template #action>
      <NButton
        v-permission="'post/api/v1/finance/recharge/create'"
        type="primary"
        @click="handleAddWrapper"
      >
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建充值
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRechargeList"
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
        <QueryBarItem label="支付状态" :label-width="80">
          <NSelect
            v-model:value="queryItems.is_paid"
            clearable
            placeholder="请选择支付状态"
            :options="[
              { label: '已支付', value: true },
              { label: '未支付', value: false },
            ]"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
    <!-- 新建充值 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      :show-save="false"
    >
      <template #footer>
        <template v-if="step === 1">
          <NButton @click="modalVisible = false">取消</NButton>
          <NButton type="primary" :loading="modalLoading" @click="handlePayment">下一步</NButton>
        </template>
        <template v-else-if="step === 2">
          <span></span>
        </template>
      </template>

      <!-- 步骤1：填写充值信息 -->
      <NForm
        v-if="step === 1"
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="100"
        :model="modalForm"
        :rules="validateRecharge"
      >
        <NFormItem label="用户ID" path="user_id">
          <NInput v-model:value="modalForm.user_id" clearable placeholder="请输入用户ID" />
        </NFormItem>
        <NFormItem label="充值金额" path="amount">
          <NInputNumber
            v-model:value="modalForm.amount"
            :min="0.01"
            :precision="2"
            placeholder="请输入充值金额"
            class="w-full"
          >
            <template #suffix>元</template>
          </NInputNumber>
        </NFormItem>
        <NFormItem label="支付方式" path="payment_method">
          <NRadioGroup v-model:value="modalForm.payment_method">
            <NRadio value="wechat">微信支付</NRadio>
            <NRadio value="alipay">支付宝</NRadio>
          </NRadioGroup>
        </NFormItem>
      </NForm>
      <!-- 步骤2：显示二维码 -->
      <div v-if="step === 2" class="text-center">
        <NAlert type="info" class="mb-20px">
          请使用{{
            modalForm.payment_method === 'alipay' ? '支付宝' : '微信'
          }}扫描下方二维码，完成支付后点击下方按钮
        </NAlert>
        <div v-if="qrCodeUrl" class="mb-20px flex justify-center">
          <QRCode :value="qrCodeUrl" :size="224" level="H" class="border rounded-lg" />
        </div>
        <NDescriptions bordered :column="3" class="mb-20px">
          <NDescriptionsItem label="订单号">{{ modalForm.trade_id }}</NDescriptionsItem>
          <NDescriptionsItem label="充值金额">{{ modalForm.amount }} 元</NDescriptionsItem>
          <NDescriptionsItem label="获得积分">{{ modalForm.points }} 积分</NDescriptionsItem>
        </NDescriptions>
        <NButton
          type="primary"
          :loading="isPolling"
          :disabled="paymentCompleted"
          @click="checkPaymentStatus"
        >
          {{ paymentCompleted ? '支付成功！' : isPolling ? '查询中...' : '已完成支付' }}
        </NButton>
      </div>
    </CrudModal>
    <!-- 退款弹窗 -->
    <NModal
      v-model:show="refundModalVisible"
      preset="dialog"
      title="退款"
      :positive-text="'确定'"
      :negative-text="'取消'"
      :loading="refundModalLoading"
      @positive-click="handleRefundSubmit"
    >
      <NForm
        ref="refundFormRef"
        :model="refundForm"
        :rules="validateRefund"
        label-placement="left"
        label-width="100"
        style="margin-top: 20px"
      >
        <NFormItem label="订单号">
          <span>{{ refundForm.trade_id }}</span>
        </NFormItem>
        <NFormItem label="原支付金额">
          <span>{{ currentRechargeRow?.amount }} 元</span>
        </NFormItem>
        <NFormItem label="退款金额" path="amount">
          <NInputNumber
            v-model:value="refundForm.amount"
            :min="0.01"
            :max="currentRechargeRow?.amount"
            :precision="2"
            placeholder="请输入退款金额"
            class="w-full"
          >
            <template #suffix>元</template>
          </NInputNumber>
        </NFormItem>
        <NFormItem label="退款原因">
          <NInput
            v-model:value="refundForm.reason"
            type="textarea"
            placeholder="请输入退款原因（可选）"
            :autosize="{ minRows: 3, maxRows: 5 }"
          />
        </NFormItem>
      </NForm>
    </NModal>
  </CommonPage>
</template>
