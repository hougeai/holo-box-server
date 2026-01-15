<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NRadio,
  NRadioGroup,
  NForm,
  NFormItem,
  NInput,
  NSpace,
  NSwitch,
  NTag,
  NPopconfirm,
} from 'naive-ui'

import { formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'

import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue' // 根据size color等参数动态渲染图标
import { useUserStore } from '@/store'

defineOptions({ name: '用户管理' })

const $table = ref(null) // 只是说明这是一个特殊的实例
const queryItems = ref({})
const vPermission = resolveDirective('permission') // 用来解析自定义指令，是app.directive('permission', {})定义的

const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '用户',
  initForm: {},
  doCreate: api.createUser,
  doUpdate: api.updateUser,
  doDelete: api.deleteUser,
  refresh: () => $table.value?.handleSearch(), // 在CrudTable中定义的
})

const roleOption = ref([])

onMounted(() => {
  $table.value?.handleSearch()
  api.getRoleList({ page: 1, page_size: 9999 }).then((res) => {
    roleOption.value = res.data
  })
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
    title: '名称',
    key: 'user_name',
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
    title: '微信ID',
    key: 'wxid',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '邮箱',
    key: 'email',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '手机',
    key: 'phone',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '知识库ID',
    key: 'kb_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '用户角色',
    key: 'role',
    width: 40,
    align: 'center',
    render(row) {
      const role_id = row.role_id ?? 0
      const role = roleOption.value.find((r) => r.id === role_id)
      return h(
        NTag,
        { type: 'info', style: { margin: '2px 3px' } },
        { default: () => role?.name || '未分配' },
      )
    },
  },
  {
    title: '注册时间',
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
    title: '上次登录时间',
    key: 'last_login',
    align: 'center',
    width: 70,
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () => (row.last_login !== null ? formatDateTime(row.last_login) : null),
        },
      )
    },
  },
  {
    title: '禁用',
    key: 'is_active',
    width: 40,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_active,
        loading: !!row.publishing, // 将变量强制转换为布尔值
        checkedValue: false,
        uncheckedValue: true,
        onUpdateValue: () => handleUpdateDisable(row),
      })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
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
                modalForm.value.role_id = row.role_id
              },
            },
            {
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            },
          ),
          [[vPermission, 'post/api/v1/user/update']],
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ user_id: row.user_id }, false),
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
                [[vPermission, 'delete/api/v1/user/delete']],
              ),
            default: () => h('div', {}, '确定删除该用户吗?'),
          },
        ),
        !row.is_superuser &&
          h(
            NPopconfirm,
            {
              onPositiveClick: async () => {
                try {
                  await api.resetPassword({ user_id: row.id })
                  $message.success('密码已成功重置')
                  await $table.value?.handleSearch()
                } catch (error) {
                  $message.error('重置密码失败: ' + error.message)
                }
              },
              onNegativeClick: () => {},
            },
            {
              trigger: () =>
                withDirectives(
                  h(
                    NButton,
                    {
                      size: 'small',
                      type: 'warning',
                      style: 'margin-right: 8px;',
                    },
                    {
                      default: () => '重置密码',
                      icon: renderIcon('material-symbols:lock-reset', { size: 16 }),
                    },
                  ),
                  [[vPermission, 'post/api/v1/user/reset_password']],
                ),
              default: () => h('div', {}, '确定重置用户密码吗?'),
            },
          ),
      ]
    },
  },
]

// 修改用户禁用状态
async function handleUpdateDisable(row) {
  if (!row.id) return
  const userStore = useUserStore()
  if (userStore.userId === row.id) {
    $message.error('当前登录用户不可禁用！')
    return
  }
  row.publishing = true
  row.is_active = !row.is_active
  row.publishing = false
  try {
    await api.updateUser(row)
    $message?.success(row.is_active ? '已取消禁用该用户' : '已禁用该用户')
    $table.value?.handleSearch()
  } catch (err) {
    // 有异常恢复原来的状态
    console.error(err)
    row.is_active = !row.is_active
  } finally {
    row.publishing = false
  }
}

const validateAddUser = {
  username: [
    {
      required: true,
      message: '请输入名称',
      trigger: ['input', 'blur'],
    },
  ],
  email: [
    {
      required: false,
      message: '请输入邮箱地址',
      trigger: ['input', 'change'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        // 如果值为空，则不进行格式验证
        if (!value) {
          return callback()
        }
        const re = /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/
        if (!re.test(modalForm.value.email)) {
          callback('邮箱格式错误')
          return
        }
        callback()
      },
    },
  ],
  phone: [
    {
      required: false,
      message: '请输入手机号码',
      trigger: ['input', 'change'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        // 如果值为空，则不进行格式验证
        if (!value) {
          return callback()
        }
        const re = /^1[3-9]\d{9}$/
        if (!re.test(value)) {
          callback('手机号格式错误')
          return
        }
        callback()
      },
    },
  ],
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirmPassword: [
    {
      required: true,
      message: '请再次输入密码',
      trigger: ['input'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        if (value !== modalForm.value.password) {
          callback('两次密码输入不一致')
          return
        }
        callback()
      },
    },
  ],
  role_id: [
    {
      type: 'number',
      required: true,
      message: '请选择一个角色',
      trigger: ['blur', 'change'],
    },
  ],
}
</script>

<template>
  <CommonPage show-footer title="用户列表">
    <template #action>
      <NButton v-permission="'post/api/v1/user/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建用户
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getUserList"
    >
      <template #queryBar>
        <QueryBarItem label="ID" :label-width="20">
          <NInput
            v-model:value="queryItems.user_id"
            clearable
            type="text"
            placeholder="请输入用户ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="角色" :label-width="30">
          <NInput
            v-model:value="queryItems.role_id"
            clearable
            type="text"
            placeholder="请输入角色ID"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="名称" :label-width="30">
          <NInput
            v-model:value="queryItems.user_name"
            clearable
            type="text"
            placeholder="请输入用户名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="邮箱" :label-width="30">
          <NInput
            v-model:value="queryItems.email"
            clearable
            type="text"
            placeholder="请输入邮箱"
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
        :rules="validateAddUser"
      >
        <NFormItem label="用户名称" path="user_name">
          <NInput v-model:value="modalForm.username" clearable placeholder="请输入用户名称" />
        </NFormItem>
        <NFormItem label="邮箱" path="email">
          <NInput v-model:value="modalForm.email" clearable placeholder="请输入邮箱" />
        </NFormItem>
        <NFormItem label="手机" path="phone">
          <NInput v-model:value="modalForm.phone" clearable placeholder="请输入手机号" />
        </NFormItem>
        <NFormItem v-if="modalAction === 'add'" label="密码" path="password">
          <NInput
            v-model:value="modalForm.password"
            show-password-on="mousedown"
            type="password"
            clearable
            placeholder="请输入密码"
          />
        </NFormItem>
        <NFormItem v-if="modalAction === 'add'" label="确认密码" path="confirmPassword">
          <NInput
            v-model:value="modalForm.confirmPassword"
            show-password-on="mousedown"
            type="password"
            clearable
            placeholder="请确认密码"
          />
        </NFormItem>
        <NFormItem label="角色" path="role_id">
          <NRadioGroup v-model:value="modalForm.role_id">
            <NSpace item-style="display: flex;">
              <NRadio
                v-for="item in roleOption"
                :key="item.id"
                :value="item.id"
                :label="item.name"
              />
            </NSpace>
          </NRadioGroup>
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
