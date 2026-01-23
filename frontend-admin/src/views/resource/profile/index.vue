<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives, onBeforeUnmount, computed } from 'vue'
import {
  NButton,
  NInput,
  NPopconfirm,
  NPopover,
  NTag,
  NModal,
  NTabs,
  NTabPane,
  NFormItem,
  NUpload,
  NProgress,
  NDivider,
  NSpin,
} from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDate, renderIcon, formatJSON } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: '形象管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const userStore = useUserStore()

// 创建形象对话框
const createModalVisible = ref(false)
const activeTab = ref('upload')

// 用户上传方式状态
const uploadForm = ref({
  name: '',
  uploadingImg: false,
  uploadingVideo: false,
  profileId: null,
  oriImgUrl: null,
  oriImgFile: null,
  uploadedVideos: {},
  selectedVideos: {},
})

// AIGC生成方式状态
const aigcForm = ref({
  name: '',
  uploadingImg: false,
  profileId: null,
  oriImgUrl: null,
  oriImgFile: null,
  genImgUrl: null,
  generating: false,
  generateProgress: 0,
  generateStatus: 'default',
})

// 情绪列表
const emotions = [
  { key: 'happy', label: '开心' },
  { key: 'sad', label: '悲伤' },
  { key: 'angry', label: '愤怒' },
  { key: 'love', label: '爱意' },
  { key: 'surprised', label: '惊讶' },
  { key: 'shocked', label: '震惊' },
  { key: 'neutral', label: '自然' },
  { key: 'calm', label: '平静' },
  { key: 'playful', label: '顽皮' },
  { key: 'embarrassed', label: '害羞' },
]

// 轮询定时器
let pollTimer = null

const { modalVisible, modalTitle, modalLoading, handleSave, modalForm, handleEdit, handleDelete } =
  useCRUD({
    name: 'Profile',
    initForm: {
      user_id: userStore.userId,
    },
    doUpdate: api.updateProfile,
    doDelete: api.deleteProfile,
    refresh: () => $table.value?.handleSearch(),
  })

// 打开创建对话框
const openCreateModal = () => {
  createModalVisible.value = true
  activeTab.value = 'upload'
  resetUploadForm()
  resetAigcForm()
}

// 重置用户上传表单
const resetUploadForm = () => {
  uploadForm.value = {
    name: '',
    uploadingImg: false,
    uploadingVideo: false,
    profileId: null,
    oriImgUrl: null,
    oriImgFile: null,
    uploadedVideos: {},
    selectedVideos: {},
  }
}

// 重置AIGC表单
const resetAigcForm = () => {
  aigcForm.value = {
    name: '',
    uploadingImg: false,
    profileId: null,
    oriImgUrl: null,
    oriImgFile: null,
    genImgUrl: null,
    generating: false,
    generateProgress: 0,
    generateStatus: 'default',
  }
}

// 用户上传：选择原始图片预览
const handleSelectOriImg = (e) => {
  const file = e.file.file
  uploadForm.value.oriImgFile = file
  uploadForm.value.oriImgUrl = URL.createObjectURL(file)
}

// 用户上传：上传原始图片
const handleUploadOriImg = async () => {
  if (!uploadForm.value.name) {
    $message.warning('请输入形象名称')
    return
  }
  if (!uploadForm.value.oriImgFile) {
    $message.warning('请先选择图片')
    return
  }
  const formData = new FormData()
  formData.append('name', uploadForm.value.name)
  formData.append('ori_img', uploadForm.value.oriImgFile)
  formData.append('ret_gen_img', 'false')

  try {
    uploadForm.value.uploadingImg = true
    const res = await api.profileUploadImg(formData)
    if (res.code === 200) {
      uploadForm.value.profileId = res.data.id
      uploadForm.value.oriImgUrl = res.data.ori_img
      $message.success('原始图片上传成功，请上传情绪视频')
    } else {
      $message.error(res.msg || '上传失败')
    }
  } catch {
    $message.error('上传失败')
  } finally {
    uploadForm.value.uploadingImg = false
  }
}

// 用户上传：选择视频
const handleSelectVideo = (fileList, emotion) => {
  const file = fileList.fileList[fileList.fileList.length - 1]?.file
  if (file) {
    const newSelectedVideos = { ...uploadForm.value.selectedVideos }
    newSelectedVideos[emotion] = file
    uploadForm.value.selectedVideos = newSelectedVideos
  }
}
// 计算所有视频是否选择完成
const allVideosSelected = computed(() => {
  return emotions.every((e) => uploadForm.value.selectedVideos[e.key])
})

// 计算所有视频是否上传完成
const allVideosUploaded = computed(() => {
  return emotions.every((e) => uploadForm.value.uploadedVideos[e.key])
})

// 用户上传：上传所有选定的视频
const handleUploadAllVideos = async () => {
  if (!allVideosSelected.value) {
    $message.warning('请先选择所有视频')
    return
  }

  uploadForm.value.uploadingVideo = true

  try {
    for (const emotion of emotions) {
      if (!uploadForm.value.uploadedVideos[emotion.key]) {
        const formData = new FormData()
        formData.append('id', uploadForm.value.profileId)
        formData.append('emotion', emotion.key)
        formData.append('video', uploadForm.value.selectedVideos[emotion.key])

        const res = await api.profileUploadVid(formData)
        if (res.code === 200) {
          uploadForm.value.uploadedVideos[emotion.key] = res.data.video_url
          $message.success(`${emotion.label}视频上传成功`)
        } else {
          $message.error(`${emotion.label}视频上传失败: ${res.msg}`)
        }
      }
    }
    $message.success('所有视频上传完成')
  } catch (error) {
    console.error(error)
    $message.error('上传过程中出现错误')
  } finally {
    uploadForm.value.uploadingVideo = false
  }
}

// 用户上传：完成创建
const finishUpload = async () => {
  try {
    const res = await api.updateProfile({
      id: uploadForm.value.profileId,
      gen_vids: uploadForm.value.uploadedVideos,
      status: 'success',
    })
    if (res.code === 200) {
      $message.success('形象创建成功')
      createModalVisible.value = false
      $table.value?.handleSearch()
    } else {
      $message.error(res.msg || '创建失败')
    }
  } catch {
    $message.error('创建失败')
  }
}

// AIGC生成：选择原始图片预览
const handleAIGCSelectOriImg = (e) => {
  const file = e.file.file
  aigcForm.value.oriImgFile = file
  aigcForm.value.oriImgUrl = URL.createObjectURL(file)
}

// AIGC生成：上传原始图片并生成图片
const handleAIGCUploadOriImg = async () => {
  if (!aigcForm.value.name) {
    $message.warning('请输入形象名称')
    return
  }
  if (!aigcForm.value.oriImgFile) {
    $message.warning('请先选择图片')
    return
  }
  const formData = new FormData()
  formData.append('name', aigcForm.value.name)
  formData.append('ori_img', aigcForm.value.oriImgFile)
  formData.append('ret_gen_img', 'true')

  try {
    aigcForm.value.uploadingImg = true
    const res = await api.profileUploadImg(formData)
    if (res.code === 200) {
      aigcForm.value.profileId = res.data.id
      aigcForm.value.oriImgUrl = res.data.ori_img
      aigcForm.value.genImgUrl = res.data.gen_img
      $message.success('原始图片上传成功，形象图片已生成，可开始生成视频')
    } else {
      $message.error(res.msg || '上传失败')
    }
  } catch {
    $message.error('上传失败')
  } finally {
    aigcForm.value.uploadingImg = false
  }
}

// AIGC生成：开始生成视频
const startGenerate = async () => {
  try {
    aigcForm.value.generating = true
    aigcForm.value.generateProgress = 0
    aigcForm.value.generateStatus = 'default'

    const res = await api.profileGenerateVid({
      id: aigcForm.value.profileId,
      method: 'bailian',
    })

    if (res.code === 200) {
      $message.success('视频生成任务已提交，正在生成中...')
      startPolling()
    } else {
      $message.error(res.msg || '任务提交失败')
      aigcForm.value.generating = false
    }
  } catch {
    $message.error('任务提交失败')
    aigcForm.value.generating = false
  }
}

// AIGC生成：轮询状态
const startPolling = () => {
  const maxRetries = 60 // 最多轮询60次，每次2秒，共2分钟
  let retryCount = 0

  pollTimer = setInterval(async () => {
    try {
      const res = await api.getProfile({ id: aigcForm.value.profileId })
      if (res.code === 200) {
        const profile = res.data
        retryCount++

        // 计算进度
        const completedCount = profile.gen_vids
          ? Object.values(profile.gen_vids).filter((v) => v.url).length
          : 0
        aigcForm.value.generateProgress = Math.floor((completedCount / emotions.length) * 100)

        if (profile.status === 'success') {
          clearInterval(pollTimer)
          aigcForm.value.generating = false
          aigcForm.value.generateStatus = 'success'
          aigcForm.value.generateProgress = 100
          $message.success('形象视频生成完成')
          createModalVisible.value = false
          $table.value?.handleSearch()
        } else if (retryCount >= maxRetries) {
          clearInterval(pollTimer)
          aigcForm.value.generating = false
          aigcForm.value.generateStatus = 'error'
          $message.warning('生成超时，请稍后查看')
        }
      }
    } catch (e) {
      console.error('轮询失败:', e)
    }
  }, 2000)
}

// 组件卸载时清除定时器
onBeforeUnmount(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
  }
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
    title: '形象名称',
    key: 'name',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '原始图片',
    key: 'ori_img',
    width: 30,
    align: 'center',
    render: (row) => {
      return row.ori_img
        ? h('img', {
            src: row.ori_img,
            style:
              'width: 50px; height: 50px; object-fit: cover; border-radius: 4px; cursor: pointer;',
            onClick: () => window.open(row.ori_img, '_blank'),
          })
        : h('span', { style: 'color: #ccc;' }, '-')
    },
  },
  {
    title: '生成图片',
    key: 'gen_img',
    width: 30,
    align: 'center',
    render: (row) => {
      return row.gen_img
        ? h('img', {
            src: row.gen_img,
            style:
              'width: 50px; height: 50px; object-fit: cover; border-radius: 4px; cursor: pointer;',
            onClick: () => window.open(row.gen_img, '_blank'),
          })
        : h('span', { style: 'color: #ccc;' }, '-')
    },
  },
  {
    title: '形象视频',
    key: 'body',
    align: 'center',
    width: 30,
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
              formatJSON(row.gen_vids),
            ),
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
      return h(
        NTag,
        { type: row.public ? 'success' : 'default' },
        { default: () => (row.public ? '是' : '否') },
      )
    },
  },
  {
    title: '方法',
    key: 'method',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '状态',
    key: 'status',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
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
          default: () => (row.create_at !== null ? formatDate(row.create_at) : null),
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
          [[vPermission, 'post/api/v1/profile/update']],
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
                [[vPermission, 'delete/api/v1/profile/delete']],
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
  <CommonPage show-footer title="形象列表">
    <template #action>
      <NButton type="primary" @click="openCreateModal">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建形象
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getProfileList"
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
        <QueryBarItem label="形象名称" :label-width="60">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入形象名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 创建形象对话框 -->
    <NModal
      v-model:show="createModalVisible"
      preset="card"
      title="新建形象"
      :style="{ width: '800px' }"
      :mask-closable="false"
    >
      <NTabs v-model:value="activeTab" type="line">
        <!-- 用户上传 Tab -->
        <NTabPane name="upload" tab="用户上传">
          <NSpin :show="uploadForm.uploadingImg">
            <NFormItem label="形象名称">
              <NInput
                v-model:value="uploadForm.name"
                placeholder="请输入形象名称"
                :disabled="!!uploadForm.profileId"
              />
            </NFormItem>
            <NFormItem label="原始图片">
              <div class="img-preview-wrapper">
                <img v-if="uploadForm.oriImgUrl" :src="uploadForm.oriImgUrl" class="w-80 h-80" />
                <div v-else class="img-placeholder">暂无图片</div>
                <div class="upload-actions">
                  <NUpload
                    :show-file-list="false"
                    :disabled="!!uploadForm.profileId || uploadForm.uploadingImg"
                    accept="image/*"
                    :on-change="handleSelectOriImg"
                  >
                    <NButton :disabled="!!uploadForm.profileId || uploadForm.uploadingImg">
                      <TheIcon icon="material-symbols:upload" :size="16" class="mr-5" />选择图片
                    </NButton>
                  </NUpload>
                  <NButton
                    v-if="uploadForm.oriImgFile && !uploadForm.profileId"
                    type="primary"
                    :disabled="uploadForm.uploadingImg"
                    :loading="uploadForm.uploadingImg"
                    @click="handleUploadOriImg"
                  >
                    上传
                  </NButton>
                </div>
              </div>
            </NFormItem>
          </NSpin>

          <NDivider v-if="uploadForm.profileId">上传情绪视频（10种）</NDivider>

          <div v-if="uploadForm.profileId" class="grid grid-cols-5 gap-4">
            <div
              v-for="emotion in emotions"
              :key="emotion.key"
              class="flex flex-col items-center text-center"
            >
              <div class="flex flex-col items-center w-full">
                <div class="w-full text-center font-medium mb-2">{{ emotion.label }}</div>
                <NUpload
                  :show-file-list="false"
                  accept="video/*"
                  :on-change="(fileList) => handleSelectVideo(fileList, emotion.key)"
                  class="w-full"
                >
                  <NButton size="small" class="w-full mb-2"> 添加{{ emotion.label }}视频 </NButton>
                </NUpload>
                <div
                  v-if="uploadForm.selectedVideos[emotion.key]"
                  class="mt-1 text-gray-500 break-all"
                >
                  {{ uploadForm.selectedVideos[emotion.key].name }}
                </div>
                <span v-if="uploadForm.uploadedVideos[emotion.key]" class="text-green"
                  >✓ 已上传</span
                >
              </div>
            </div>

            <div class="col-span-5 flex justify-center gap-8">
              <NButton
                type="primary"
                :disabled="!allVideosSelected || uploadForm.uploadingVideo"
                :loading="uploadForm.uploadingVideo"
                @click="handleUploadAllVideos"
              >
                {{ uploadForm.uploadingVideo ? '上传中...' : '批量上传视频' }}
              </NButton>
              <NButton type="primary" :disabled="!allVideosUploaded" @click="finishUpload">
                创建形象
              </NButton>
            </div>
          </div>
        </NTabPane>

        <!-- AIGC生成 Tab -->
        <NTabPane name="aigc" tab="AIGC生成">
          <NSpin :show="aigcForm.uploadingImg">
            <NFormItem label="形象名称">
              <NInput
                v-model:value="aigcForm.name"
                placeholder="请输入形象名称"
                :disabled="!!aigcForm.profileId"
              />
            </NFormItem>
            <NFormItem label="原始图片">
              <div class="img-preview-wrapper">
                <img v-if="aigcForm.oriImgUrl" :src="aigcForm.oriImgUrl" class="w-80 h-80" />
                <div v-else class="img-placeholder">暂无图片</div>
                <div class="upload-actions">
                  <NUpload
                    :show-file-list="false"
                    :disabled="!!aigcForm.profileId || aigcForm.uploadingImg"
                    accept="image/*"
                    :on-change="handleAIGCSelectOriImg"
                  >
                    <NButton :disabled="!!aigcForm.profileId || aigcForm.uploadingImg">
                      <TheIcon icon="material-symbols:upload" :size="16" class="mr-5" />选择图片
                    </NButton>
                  </NUpload>
                  <NButton
                    v-if="aigcForm.oriImgFile && !aigcForm.profileId"
                    type="primary"
                    :disabled="aigcForm.uploadingImg"
                    :loading="aigcForm.uploadingImg"
                    @click="handleAIGCUploadOriImg"
                  >
                    上传
                  </NButton>
                </div>
              </div>
            </NFormItem>
            <NFormItem v-if="aigcForm.genImgUrl" label="生成图片">
              <div class="img-preview-wrapper">
                <img :src="aigcForm.genImgUrl" class="w-80 h-80" />
              </div>
            </NFormItem>
          </NSpin>

          <NDivider v-if="aigcForm.profileId">生成情绪视频</NDivider>

          <div v-if="aigcForm.profileId">
            <p>将为您自动生成10种情绪的视频，完成后即可使用形象</p>
            <NButton
              type="primary"
              :loading="aigcForm.generating"
              :disabled="aigcForm.generating"
              @click="startGenerate"
            >
              开始生成
            </NButton>
            <NProgress
              v-if="aigcForm.generating"
              type="line"
              :percentage="aigcForm.generateProgress"
              :status="aigcForm.generateStatus"
              class="mt-4"
            />
          </div>
        </NTabPane>
      </NTabs>
    </NModal>

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
        :disabled="modalAction === 'view'"
      >
        <NFormItem
          label="形象名称"
          path="name"
          :rule="{
            required: true,
            message: '请输入形象名称',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput v-model:value="modalForm.name" placeholder="请输入形象名称" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>

<style scoped>
.img-preview-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.img-placeholder {
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed #d9d9d9;
  border-radius: 4px;
  color: #999;
  font-size: 14px;
  flex-shrink: 0;
}

.upload-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}

.text-green {
  color: #18a058;
}

.mr-5 {
  margin-right: 5px;
}

.mt-4 {
  margin-top: 16px;
}

.ml-2 {
  margin-left: 8px;
}
</style>
