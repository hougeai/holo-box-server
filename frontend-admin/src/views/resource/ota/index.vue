<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSwitch, NPopconfirm } from 'naive-ui'

import { formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: 'OTA管理' })

const ossUrl = import.meta.env.VITE_OSS_BUCKET_URL || ''

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
  name: 'OTA版本',
  initForm: { user_id: userStore.userId },
  doCreate: api.createOta,
  doUpdate: api.updateOta,
  doDelete: api.deleteOta,
  refresh: () => $table.value?.handleSearch(), // 在CrudTable中定义的
})

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
    title: '版本号',
    key: 'app_version',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '芯片型号',
    key: 'chip_type',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '设备型号',
    key: 'device_model',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '完整固件',
    key: 'whole_url',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      if (row.whole_url) {
        return h(
          'a',
          {
            href: `${ossUrl}/${row.whole_url}`,
            target: '_blank',
            style: {
              color: 'var(--primary-color)',
              textDecoration: 'underline',
              cursor: 'pointer',
            },
          },
          { default: () => '点击下载' },
        )
      } else {
        return h('span', {}, '-') // 可以返回空内容或其他占位符
      }
    },
  },
  {
    title: 'OTA固件',
    key: 'ota_url',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      if (row.ota_url) {
        return h(
          'a',
          {
            href: `${ossUrl}/${row.ota_url}`,
            target: '_blank',
            style: {
              color: 'var(--primary-color)',
              textDecoration: 'underline',
              cursor: 'pointer',
            },
          },
          { default: () => '点击下载' },
        )
      } else {
        return h('span', {}, '-') // 可以返回空内容或其他占位符
      }
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
    title: '设为最新',
    key: 'is_default',
    width: 30,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_default,
        loading: !!row.publishing, // 将变量强制转换为布尔值
        checkedValue: true,
        uncheckedValue: false,
        onUpdateValue: () => handleUpdateDefault(row),
      })
    },
  },
  {
    title: '强制更新',
    key: 'force_update',
    width: 30,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.force_update,
        loading: !!row.publishing, // 将变量强制转换为布尔值
        checkedValue: true,
        uncheckedValue: false,
        onUpdateValue: () => handleUpdateForce(row),
      })
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
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            },
          ),
          [[vPermission, 'post/api/v1/resource/ota/update']],
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete(row),
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
                    default: () => '删除',
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  },
                ),
                [[vPermission, 'delete/api/v1/resource/ota/delete']],
              ),
            default: () => h('div', {}, '确定删除该版本吗?'),
          },
        ),
      ]
    },
  },
]

// 修改默认状态
async function handleUpdateDefault(row) {
  if (!row.id) return
  row.publishing = true
  row.is_default = !row.is_default
  row.publishing = false
  try {
    await api.updateOta(row)
    $message?.success(row.is_default ? '已设为最新' : '已取消最新')
    $table.value?.handleSearch()
  } catch (error) {
    // 有异常恢复原来的状态
    row.is_default = !row.is_default
    console.error(error)
  } finally {
    row.publishing = false
  }
}
// 修改强制更新状态
async function handleUpdateForce(row) {
  if (!row.id) return
  row.publishing = true
  row.force_update = !row.force_update
  row.publishing = false
  try {
    await api.updateOta(row)
    $message?.success(row.force_update ? '已设为强制更新' : '已取消强制更新')
    $table.value?.handleSearch()
  } catch (error) {
    // 有异常恢复原来的状态
    row.force_update = !row.force_update
    console.error(error)
  } finally {
    row.publishing = false
  }
}
// 表单验证规则
const validateAdd = {
  appVersion: [
    {
      required: true,
      message: '请输入版本号',
      trigger: ['input', 'blur'],
    },
  ],
  chipType: [
    {
      required: true,
      message: '请输入芯片型号',
      trigger: ['input', 'blur'],
    },
  ],
  deviceModel: [
    {
      required: true,
      message: '请输入设备型号',
      trigger: ['input', 'blur'],
    },
  ],
}

// 添加文件上传相关的变量
const wholeTempFile = ref(null)
const wholeTempFileUrl = ref('')
const otaTempFile = ref(null)
const otaTempFileUrl = ref('')

// 处理文件上传
const handleWholeFileChange = (file) => {
  if (file.file) {
    // 验证文件大小（例如10MB限制）
    if (file.file.size > 10 * 1024 * 1024) {
      $message.error('文件大小不能超过10MB')
      return
    }
    wholeTempFile.value = file.file.file
    wholeTempFileUrl.value = URL.createObjectURL(file.file.file)
  }
}
const handleOtaFileChange = (file) => {
  if (file.file) {
    // 验证文件大小（例如10MB限制）
    if (file.file.size > 10 * 1024 * 1024) {
      $message.error('文件大小不能超过10MB')
      return
    }
    otaTempFile.value = file.file.file
    otaTempFileUrl.value = URL.createObjectURL(file.file.file)
  }
}

// 处理文件删除
const handleDeleteWholeBin = async (modalForm) => {
  console.log('handleDeleteWholeBin', wholeTempFileUrl.value, modalForm.whole_url)
  if (wholeTempFileUrl.value) {
    URL.revokeObjectURL(wholeTempFileUrl.value)
    wholeTempFile.value = null
    wholeTempFileUrl.value = ''
    modalForm.whole_url = ''
    return
  }
  if (modalForm.whole_url) {
    // 清空表单数据
    modalForm.whole_url = ''
  }
}
const handleDeleteOtaBin = async (modalForm) => {
  console.log('handleDeleteOtaBin', otaTempFileUrl.value, modalForm.ota_url)
  if (otaTempFileUrl.value) {
    URL.revokeObjectURL(otaTempFileUrl.value)
    otaTempFile.value = null
    otaTempFileUrl.value = ''
    modalForm.ota_url = ''
    return
  }
  if (modalForm.ota_url) {
    // 清空表单数据
    modalForm.ota_url = ''
  }
}

// 重写handleSave方法，需给后端发送请求上传固件文件
async function handleSaveOta() {
  // 如果有新文件需要上传
  if (wholeTempFile.value) {
    try {
      const formData = new FormData()
      formData.append('file', wholeTempFile.value)
      formData.append('app_version', modalForm.value.app_version)
      formData.append('device_model', modalForm.value.device_model)
      formData.append('file_type', 'zip')

      const response = await api.uploadOtaFile(formData)
      modalForm.value.whole_url = response.data.url
    } catch (error) {
      console.error('wholeFirmware upload failed', error)
      $message.error('完整固件文件上传失败')
      return false
    }
  }
  if (otaTempFile.value) {
    try {
      const formData = new FormData()
      formData.append('file', otaTempFile.value)
      formData.append('app_version', modalForm.value.app_version)
      formData.append('device_model', modalForm.value.device_model)
      formData.append('file_type', 'bin')

      const response = await api.uploadOtaFile(formData)
      modalForm.value.ota_url = response.data.url
    } catch (error) {
      console.error('otaFirmware upload failed', error)
      $message.error('OTA固件文件上传失败')
      return false
    }
  }
  // 清理临时文件
  if (wholeTempFileUrl.value) {
    URL.revokeObjectURL(wholeTempFileUrl.value)
    wholeTempFile.value = null
    wholeTempFileUrl.value = ''
  }
  if (otaTempFileUrl.value) {
    URL.revokeObjectURL(otaTempFileUrl.value)
    otaTempFile.value = null
    otaTempFileUrl.value = ''
  }
  return true
}
</script>

<template>
  <CommonPage show-footer title="固件列表">
    <template #action>
      <NButton v-permission="'post/api/v1/resource/ota/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新增OTA版本
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getOtaList"
    >
      <template #queryBar>
        <QueryBarItem label="版本号" :label-width="60">
          <NInput
            v-model:value="queryItems.app_version"
            clearable
            type="text"
            placeholder="请输入版本号"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="芯片型号" :label-width="60">
          <NInput
            v-model:value="queryItems.chip_type"
            clearable
            type="text"
            placeholder="请输入芯片型号"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="设备型号" :label-width="60">
          <NInput
            v-model:value="queryItems.device_model"
            clearable
            type="text"
            placeholder="请输入设备型号"
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
      @save="() => handleSave(handleSaveOta)"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="validateAdd"
      >
        <NFormItem label="版本号" path="app_version">
          <NInput v-model:value="modalForm.app_version" clearable placeholder="请输入版本号" />
        </NFormItem>
        <NFormItem label="芯片型号" path="chip_type">
          <NInput v-model:value="modalForm.chip_type" clearable placeholder="请输入芯片型号" />
        </NFormItem>
        <NFormItem label="设备型号" path="device_model">
          <NInput v-model:value="modalForm.device_model" clearable placeholder="请输入设备型号" />
        </NFormItem>
        <NFormItem label="完整固件">
          <div
            v-if="modalForm.whole_url || wholeTempFileUrl"
            style="display: flex; align-items: center; gap: 10px"
          >
            <a
              :href="modalForm.whole_url || wholeTempFileUrl"
              target="_blank"
              style="color: var(--primary-color); text-decoration: underline; cursor: pointer"
            >
              完整固件文件
            </a>
            <NButton size="tiny" type="error" @click="() => handleDeleteWholeBin(modalForm)">
              <template #icon>
                <TheIcon icon="material-symbols:delete-outline" />
              </template>
            </NButton>
          </div>
          <div v-else>
            <div style="margin-bottom: 10px; color: red; font-size: 12px">
              ！请上传完整固件文件(.zip结尾)
            </div>
            <NUpload accept=".zip" :show-file-list="false" @change="handleWholeFileChange">
              <NButton type="primary">
                <template #icon>
                  <TheIcon icon="material-symbols:add" />
                </template>
                上传完整固件文件
              </NButton>
            </NUpload>
          </div>
        </NFormItem>
        <NFormItem label="OTA固件">
          <div
            v-if="modalForm.ota_url || otaTempFileUrl"
            style="display: flex; align-items: center; gap: 10px"
          >
            <a
              :href="modalForm.ota_url || otaTempFileUrl"
              target="_blank"
              style="color: var(--primary-color); text-decoration: underline; cursor: pointer"
            >
              OTA固件文件
            </a>
            <NButton size="tiny" type="error" @click="() => handleDeleteOtaBin(modalForm)">
              <template #icon>
                <TheIcon icon="material-symbols:delete-outline" />
              </template>
            </NButton>
          </div>
          <div v-else>
            <div style="margin-bottom: 10px; color: red; font-size: 12px">
              ！请上传OTA固件文件(.bin结尾)
            </div>
            <NUpload accept=".bin" :show-file-list="false" @change="handleOtaFileChange">
              <NButton type="primary">
                <template #icon>
                  <TheIcon icon="material-symbols:add" />
                </template>
                上传OTA固件文件
              </NButton>
            </NUpload>
          </div>
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
