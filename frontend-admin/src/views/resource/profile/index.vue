<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives, onBeforeUnmount, computed } from 'vue'
import {
  NButton,
  NInput,
  NRadio,
  NRadioGroup,
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
  NSwitch,
  NForm,
} from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDateTime, renderIcon, formatJSON } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: '形象管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const userStore = useUserStore()

// 图片预览状态
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')
const imagePreviewTitle = ref('')

const handleImagePreview = (url, title) => {
  imagePreviewUrl.value = url
  imagePreviewTitle.value = title
  imagePreviewVisible.value = true
}

// 创建形象对话框
const createModalVisible = ref(false)
const activeTab = ref('upload')

// 用户上传方式状态
const uploadForm = ref({
  name: '',
  subjectType: 'human',
  uploadingImg: false,
  uploadingVideo: false,
  profileId: null,
  oriImgUrl: null,
  oriImgFile: null,
  genImgUrl: null,
  uploadedVideos: {},
  selectedVideos: {},
})

// 主体类型选项

// AIGC生成方式状态
const aigcForm = ref({
  name: '',
  subjectType: 'human',
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
  { key: 'laugh', label: '大笑' },
  { key: 'sad', label: '伤心' },
  { key: 'angry', label: '生气' },
  { key: 'love', label: '喜欢' },
  { key: 'embarrassed', label: '尴尬' },
  { key: 'thinking', label: '思考' },
  { key: 'playful', label: '调皮' },
  { key: 'calm', label: '放松' },
  { key: 'sleepy', label: '困倦' },
]

// 轮询定时器
let pollTimer = null

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
} = useCRUD({
  name: '形象',
  initForm: {
    user_id: userStore.userId,
    public: null,
    gen_vids: {},
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
    subjectType: 'human',
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
    subjectType: 'human',
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
  formData.append('ret_gen_img', true)
  formData.append('subject_type', uploadForm.value.subjectType)

  try {
    uploadForm.value.uploadingImg = true
    const res = await api.profileUploadImg(formData)
    if (res.code === 200) {
      uploadForm.value.profileId = res.data.id
      uploadForm.value.oriImgUrl = res.data.ori_img
      uploadForm.value.genImgUrl = res.data.gen_img
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
          uploadForm.value.uploadedVideos[emotion.key] = {
            url: res.data.video_url,
            hash: res.data.video_hash,
            status: 'success',
            msg: '',
          }
          $message.success(`${emotion.label}视频上传成功`)
        } else {
          uploadForm.value.uploadedVideos[emotion.key] = {
            url: '',
            hash: '',
            status: 'failed',
            msg: res.msg || '上传失败',
          }
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
      gen_img: uploadForm.value.oriImgUrl,
      gen_vids: uploadForm.value.uploadedVideos,
      method: 'upload',
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
  formData.append('ret_gen_img', true)
  formData.append('subject_type', aigcForm.value.subjectType)

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
  const maxRetries = 60 // 最多轮询6*10次，每次10秒
  let retryCount = 0

  pollTimer = setInterval(async () => {
    try {
      const res = await api.getProfile({ id: aigcForm.value.profileId })
      if (res.code === 200) {
        const profile = res.data
        retryCount++

        // 根据轮询次数估算进度，总轮询次数为maxRetries
        aigcForm.value.generateProgress = Math.floor((retryCount / maxRetries) * 100)
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
  }, 10000)
}

// 编辑模式
const editVideoUping = ref({})
const editVideoGening = ref({})
// 编辑模式：上传视频
const handleEditVideoUpload = async (emotion, fileList) => {
  const file = fileList?.fileList?.[fileList.fileList.length - 1]?.file
  if (!file) return

  editVideoUping.value[emotion] = true
  const formData = new FormData()
  formData.append('id', modalForm.value.id)
  formData.append('emotion', emotion)
  formData.append('video', file)

  try {
    const res = await api.profileUploadVid(formData)
    if (res.code === 200) {
      if (!modalForm.value.gen_vids) {
        modalForm.value.gen_vids = {}
      }
      modalForm.value.gen_vids[emotion] = {
        url: res.data.video_url,
        hash: res.data.video_hash,
        status: 'success',
        msg: '',
      }
      $message.success(`${emotions.find((e) => e.key === emotion).label}视频更新成功`)
    } else {
      $message.error(res.msg || '视频上传失败')
    }
  } catch (error) {
    console.error(error)
    $message.error('视频上传失败')
  } finally {
    editVideoUping.value[emotion] = false
  }
}

// 编辑模式：生成视频
const handleGenerateVideo = async (emotion) => {
  editVideoGening.value[emotion] = true

  try {
    const res = await api.profileGenerateVidEdit({
      id: modalForm.value.id,
      method: 'bailian',
      emotion: emotion,
    })

    if (res.code === 200) {
      if (!modalForm.value.gen_vids) {
        modalForm.value.gen_vids = {}
      }
      modalForm.value.gen_vids[emotion] = {
        url: res.data.video_url,
        hash: res.data.video_hash,
        status: 'success',
        msg: '',
      }
      $message.success(`${emotions.find((e) => e.key === emotion).label}视频生成成功`)
    } else {
      $message.error(res.msg || '视频生成失败')
    }
  } catch (error) {
    console.error(error)
    $message.error('视频生成失败')
  } finally {
    editVideoGening.value[emotion] = false
  }
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

// 是否公开选项
const publicOptions = [
  { label: '全部', value: null },
  { label: '是', value: true },
  { label: '否', value: false },
]

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
    title: '主体类型',
    key: 'subject_type',
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
      if (!row.ori_img) {
        return h('span', { style: 'color: #ccc;' }, '-')
      }

      return h(
        'div',
        {
          style: 'position: relative; width: 50px; height: 50px;',
        },
        [
          h('img', {
            src: row.ori_img,
            style:
              'width: 50px; height: 50px; object-fit: cover; border-radius: 4px; cursor: pointer;',
          }),
          h(
            'div',
            {
              style:
                'position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; gap: 8px; background: rgba(0,0,0,0.3); border-radius: 4px; opacity: 0; transition: opacity 0.2s;',
              onMouseenter: (e) => (e.target.style.opacity = '1'),
              onMouseleave: (e) => (e.target.style.opacity = '0'),
            },
            [
              h(
                NButton,
                {
                  size: 'tiny',
                  type: 'primary',
                  text: true,
                  onClick: () => handleImagePreview(row.ori_img, '原始图片'),
                },
                { icon: renderIcon('material-symbols:visibility') },
              ),
            ],
          ),
        ],
      )
    },
  },
  {
    title: '生成图片',
    key: 'gen_img',
    width: 30,
    align: 'center',
    render: (row) => {
      if (!row.gen_img) {
        return h('span', { style: 'color: #ccc;' }, '-')
      }

      return h(
        'div',
        {
          style: 'position: relative; width: 50px; height: 50px;',
        },
        [
          h('img', {
            src: row.gen_img,
            style:
              'width: 50px; height: 50px; object-fit: cover; border-radius: 4px; cursor: pointer;',
          }),
          h(
            'div',
            {
              style:
                'position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; gap: 8px; background: rgba(0,0,0,0.3); border-radius: 4px; opacity: 0; transition: opacity 0.2s;',
              onMouseenter: (e) => (e.target.style.opacity = '1'),
              onMouseleave: (e) => (e.target.style.opacity = '0'),
            },
            [
              h(
                NButton,
                {
                  size: 'tiny',
                  type: 'primary',
                  text: true,
                  onClick: () => handleImagePreview(row.gen_img, '生成图片'),
                },
                { icon: renderIcon('material-symbols:visibility') },
              ),
            ],
          ),
        ],
      )
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
      return h(NSwitch, {
        value: row.public,
        onUpdateValue: async (value) => {
          try {
            const res = await api.updateProfile({
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
    title: '方法',
    key: 'method',
    width: 30,
    align: 'center',
    render(row) {
      return h(
        NTag,
        { type: row.method === 'bailian' ? 'success' : 'default' },
        { default: () => row.method || '-' },
      )
    },
  },
  {
    title: '状态',
    key: 'status',
    width: 30,
    align: 'center',
    render(row) {
      return h(
        NTag,
        { type: row.status === 'success' ? 'success' : 'default' },
        { default: () => row.status },
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
                handleEdit(row)
              },
            },
            {
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            },
          ),
          [[vPermission, 'post/api/v1/agent/profile/update']],
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
                    loading: modalLoading.value,
                  },
                  {
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  },
                ),
                [[vPermission, 'delete/api/v1/agent/profile/delete']],
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
        <QueryBarItem label="是否公开" :label-width="60" :content-width="140">
          <NSelect
            v-model:value="queryItems.public"
            :options="publicOptions"
            clearable
            placeholder="请选择"
            @update:value="$table?.handleSearch()"
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
        <NTabPane name="upload" tab="手动上传">
          <NSpin :show="uploadForm.uploadingImg">
            <NFormItem label="形象名称">
              <NInput
                v-model:value="uploadForm.name"
                placeholder="请输入形象名称"
                :disabled="!!uploadForm.profileId"
              />
            </NFormItem>
            <NFormItem label="主体类型">
              <NRadioGroup
                v-model:value="uploadForm.subjectType"
                :disabled="!!uploadForm.profileId"
              >
                <NRadio value="human">人物</NRadio>
                <NRadio value="animal">动物</NRadio>
              </NRadioGroup>
            </NFormItem>
            <NFormItem label="原始图片">
              <div class="flex gap-4 items-start">
                <div class="flex flex-col items-center">
                  <div class="img-preview-wrapper">
                    <img
                      v-if="uploadForm.oriImgUrl"
                      :src="uploadForm.oriImgUrl"
                      class="w-80 h-80"
                    />
                    <div v-else class="img-placeholder">暂无图片</div>
                    <div class="upload-actions mt-2">
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
                </div>

                <div v-if="uploadForm.genImgUrl" class="flex flex-col items-center">
                  <div class="img-preview-wrapper">
                    <img :src="uploadForm.genImgUrl" class="w-80 h-80" />
                  </div>
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
                  accept="video/mp4"
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
            <NFormItem label="主体类型">
              <NRadioGroup v-model:value="aigcForm.subjectType" :disabled="!!aigcForm.profileId">
                <NRadio value="human">人物</NRadio>
                <NRadio value="animal">动物</NRadio>
              </NRadioGroup>
            </NFormItem>
            <NFormItem label="原始图片">
              <div class="flex gap-4 items-start">
                <div class="flex flex-col items-center">
                  <div class="img-preview-wrapper">
                    <img v-if="aigcForm.oriImgUrl" :src="aigcForm.oriImgUrl" class="w-80 h-80" />
                    <div v-else class="img-placeholder">暂无图片</div>
                    <div class="upload-actions mt-2">
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
                </div>

                <div v-if="aigcForm.genImgUrl" class="flex flex-col items-center">
                  <div class="img-preview-wrapper">
                    <img :src="aigcForm.genImgUrl" class="w-80 h-80" />
                  </div>
                </div>
              </div>
            </NFormItem>
          </NSpin>

          <NDivider v-if="aigcForm.profileId">生成情绪视频（10种）</NDivider>

          <div v-if="aigcForm.profileId" class="flex-col justify-center items-center">
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
      width="60%"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="100"
        :model="modalForm"
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
          <NInput
            v-model:value="modalForm.name"
            placeholder="请输入形象名称"
            style="width: 140px"
          />
        </NFormItem>
        <NFormItem label="图片预览">
          <div class="flex gap-8 items-start">
            <div class="flex flex-col items-center">
              <div
                class="img-preview-wrapper cursor-pointer"
                @click="modalForm.ori_img && handleImagePreview(modalForm.ori_img, '原始图片')"
              >
                <img v-if="modalForm.ori_img" :src="modalForm.ori_img" class="w-80 h-80" />
                <div v-else class="img-placeholder">暂无原始图片</div>
              </div>
              <div class="mt-2 text-gray-600">原始图片</div>
            </div>

            <div class="flex flex-col items-center">
              <div
                class="img-preview-wrapper cursor-pointer"
                @click="modalForm.gen_img && handleImagePreview(modalForm.gen_img, '生成图片')"
              >
                <img v-if="modalForm.gen_img" :src="modalForm.gen_img" class="w-80 h-80" />
                <div v-else class="img-placeholder">暂无生成图片</div>
              </div>
              <div class="mt-2 text-gray-600">生成图片</div>
            </div>
          </div>
        </NFormItem>
        <div class="text-center font-bold mb-4">形象视频</div>
        <div v-if="modalForm.id" class="grid grid-cols-5 gap-4 w-full">
          <div
            v-for="emotion in emotions"
            :key="emotion.key"
            class="flex flex-col items-center gap-2"
          >
            <NTag type="info">{{ emotion.label }}</NTag>
            <div
              class="flex items-center justify-center w-full h-150 border-dashed border-gray-300 rounded"
            >
              <video
                v-if="modalForm.gen_vids?.[emotion.key]?.url"
                :src="modalForm.gen_vids[emotion.key].url"
                :key="modalForm.gen_vids[emotion.key].hash"
                class="max-h-full max-w-full rounded"
                controls
              />
              <span v-else class="text-gray-400">暂无视频</span>
            </div>
            <div class="flex justify-center gap-4 mt-3">
              <NUpload
                :show-file-list="false"
                accept="video/mp4"
                :on-change="(fileList) => handleEditVideoUpload(emotion.key, fileList)"
              >
                <NButton size="small" type="primary" :loading="editVideoUping[emotion.key]">
                  {{ editVideoUping[emotion.key] ? '上传中...' : '上传替换' }}
                </NButton>
              </NUpload>
              <NButton
                size="small"
                type="success"
                :loading="editVideoGening[emotion.key]"
                @click="handleGenerateVideo(emotion.key)"
              >
                {{ editVideoGening[emotion.key] ? '生成中...' : '生成替换' }}
              </NButton>
            </div>
          </div>
        </div>
      </NForm>
    </CrudModal>

    <!-- 图片预览弹窗 -->
    <NModal
      v-model:show="imagePreviewVisible"
      preset="card"
      :title="imagePreviewTitle"
      style="width: 90%; max-width: 1200px"
      :bordered="false"
      :segmented="{ content: true }"
    >
      <div class="flex justify-center items-center">
        <img :src="imagePreviewUrl" style="max-width: 100%; max-height: 80vh" />
      </div>
    </NModal>
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
