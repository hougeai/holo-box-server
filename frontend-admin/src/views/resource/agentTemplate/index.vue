<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives, computed, watch } from 'vue'
import { NButton, NInput, NPopconfirm, NSelect, NFormItem, NSwitch, NModal, NSpin } from 'naive-ui'

import { formatDateTime, renderIcon, languageMap, asrSpeedMap, ttsSpeedMap } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: '智能体模板管理' })

const $table = ref(null) // 只是说明这是一个特殊的实例
const queryItems = ref({})
const vPermission = resolveDirective('permission') // 用来解析自定义指令，是app.directive('permission', {})定义的
const userStore = useUserStore()
// 查看图片对话框
const previewVisible = ref(false)
const previewUrl = ref('')
const previewType = ref('image') // 'image' 或 'video'

// 打开预览对话框
const openPreview = (url, type = 'image') => {
  previewUrl.value = url
  previewType.value = type
  previewVisible.value = true
}

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
  name: 'AgentTemplate',
  initForm: {
    user_id: userStore.userId,
    assistant_name: '盒子',
    llm_model: 'xz-lite',
    language: 'zh',
    tts_speech_speed: 'normal',
    asr_speed: 'normal',
    tts_pitch: 0,
    memory_type: 'SHORT_TERM',
    profile_id: null,
    profile_img: '',
    profile_vid: '',
    avatar: '',
    public: null,
    order: 0,
  },
  doCreate: api.createAgentTemplate,
  doUpdate: api.updateAgentTemplate,
  doDelete: api.deleteAgentTemplate,
  refresh: () => $table.value?.handleSearch(), // 在CrudTable中定义的
})

// LLM列表
const llmList = ref([])
// Voice列表
const voiceList = ref([])
// 形象列表
const profileList = ref([])
// 系统提示词列表
const sysPromptList = ref([])
// 当前播放的音频 URL
const currentPlayingAudio = ref(null)
// 获取LLM列表
const fetchLlmList = async () => {
  try {
    const res = await api.getLlmList()
    if (res.data) {
      llmList.value = res.data
    }
  } catch (error) {
    console.error('获取LLM列表失败:', error)
  }
}

// 获取Voice列表
const fetchVoiceList = async () => {
  try {
    const res = await api.getVoiceList({ public: true })
    if (res.data) {
      voiceList.value = res.data
    }
  } catch (error) {
    console.error('获取Voice列表失败:', error)
  }
}
// 获取形象列表
const fetchProfileList = async () => {
  try {
    const res = await api.getProfileList({ user_id: userStore.userId, public: true })
    if (res.data) {
      profileList.value = res.data
    }
  } catch (error) {
    console.error('获取形象列表失败:', error)
  }
}
// 获取系统提示词列表
const fetchSysPromptList = async () => {
  try {
    const res = await api.getSysPromptList()
    if (res.data) {
      sysPromptList.value = res.data
    }
  } catch (error) {
    console.error('获取系统提示词列表失败:', error)
  }
}

// 试听音频
let currentAudioInstance = null
const handlePlayAudio = (voiceDemo) => {
  // 如果当前正在播放该音频，则停止播放
  if (currentPlayingAudio.value === voiceDemo && currentAudioInstance) {
    currentAudioInstance.pause()
    currentAudioInstance.currentTime = 0
    currentPlayingAudio.value = null
    currentAudioInstance = null
    return
  }

  // 停止之前播放的音频
  if (currentAudioInstance) {
    currentAudioInstance.pause()
    currentAudioInstance.currentTime = 0
  }

  // 播放新音频
  currentPlayingAudio.value = voiceDemo
  currentAudioInstance = new Audio(voiceDemo)
  currentAudioInstance.play().catch((err) => {
    console.error('播放失败:', err)
    currentPlayingAudio.value = null
    currentAudioInstance = null
  })

  // 监听播放结束事件
  currentAudioInstance.onended = () => {
    currentPlayingAudio.value = null
    currentAudioInstance = null
  }

  // 监听播放错误事件
  currentAudioInstance.onerror = () => {
    currentPlayingAudio.value = null
    currentAudioInstance = null
  }
}

// 根据选中的语言过滤音色
const filteredVoices = computed(() => {
  if (!modalForm.value.language) {
    return voiceList.value.map((voice) => ({
      label: `${voice.voice_name || voice.voice_id} (${languageMap[voice.language] || voice.language})`,
      value: voice.voice_id,
      voiceDemo: voice.voice_demo,
    }))
  }
  return voiceList.value
    .filter((voice) => voice.language === modalForm.value.language)
    .map((voice) => ({
      label: voice.voice_name || voice.voice_id,
      value: voice.voice_id,
      voiceDemo: voice.voice_demo,
    }))
})

// 渲染 NSelect 的选项标签
const renderVoiceLabel = (option) => {
  const isPlaying = currentPlayingAudio.value === option.voiceDemo
  return h(
    'div',
    {
      style: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
      },
    },
    [
      h('span', {}, option.label),
      h(
        NButton,
        {
          size: 'tiny',
          type: isPlaying ? 'success' : 'info',
          text: true,
          onClick: (e) => {
            e.stopPropagation()
            handlePlayAudio(option.voiceDemo)
          },
        },
        {
          icon: isPlaying
            ? renderIcon('material-symbols:pause-circle', { size: 16 })
            : renderIcon('material-symbols:play-circle', { size: 16 }),
        },
      ),
    ],
  )
}

// 是否公开选项
const publicOptions = [
  { label: '全部', value: null },
  { label: '是', value: true },
  { label: '否', value: false },
]

// 上传视频
const handleUploadVideo = async (row) => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'video/mp4'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    modalLoading.value = true
    const formData = new FormData()
    formData.append('id', row.id)
    formData.append('source', file)
    formData.append('source_type', 'profile-vid')

    try {
      const res = await api.uploadAgentTemplate(formData)
      if (res.data) {
        $message.success('上传视频成功')
        $table.value?.handleSearch()
      }
    } catch (error) {
      console.error('上传视频失败:', error)
      $message.error('上传视频失败')
    } finally {
      modalLoading.value = false
    }
  }
  input.click()
}

// 上传头像
const handleUploadAvatar = async (row) => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/png,image/jpeg,image/jpg'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    modalLoading.value = true
    const formData = new FormData()
    formData.append('id', row.id)
    formData.append('source', file)
    formData.append('source_type', 'avatar')

    try {
      const res = await api.uploadAgentTemplate(formData)
      if (res.data) {
        $message.success('上传头像成功')
        $table.value?.handleSearch()
      }
    } catch (error) {
      console.error('上传头像失败:', error)
      $message.error('上传头像失败')
    } finally {
      modalLoading.value = false
    }
  }
  input.click()
}

// 语言选项
const languageOptions = computed(() => {
  return Object.entries(languageMap).map(([value, label]) => ({ label, value }))
})

// 语速选项
const asrSpeedOptions = computed(() => {
  return Object.entries(asrSpeedMap).map(([value, label]) => ({ label, value }))
})
const ttsSpeedOptions = computed(() => {
  return Object.entries(ttsSpeedMap).map(([value, label]) => ({ label, value }))
})

// 形象选项
const profileOptions = computed(() => {
  return profileList.value.map((profile) => ({
    label: profile.name,
    value: Number(profile.id),
  }))
})

// 当前选中的profile对应的gen_img
const currentProfileGenImg = computed(() => {
  const profile = profileList.value.find((p) => p.id === modalForm.value.profile_id)
  return profile?.ori_img || ''
})

// 监听profile_id变化，同步更新profile_img
watch(
  () => modalForm.value.profile_id,
  (newVal) => {
    const profile = profileList.value.find((p) => p.id === newVal)
    if (profile?.ori_img) {
      modalForm.value.profile_img = profile.ori_img
    }
  },
  { immediate: true },
)

onMounted(async () => {
  $table.value?.handleSearch()
  await Promise.all([fetchLlmList(), fetchVoiceList(), fetchProfileList(), fetchSysPromptList()])
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
    title: '模板ID',
    key: 'agent_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '模板名称',
    key: 'agent_name',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'LLM',
    key: 'llm_model',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '音色',
    key: 'tts_voice',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      const voice = voiceList.value.find((v) => v.voice_id === row.tts_voice)
      return h('span', {}, voice ? voice.voice_name || voice.voice_id : row.tts_voice || '-')
    },
  },
  {
    title: '形象ID',
    key: 'profile_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '形象图片',
    key: 'profile_img',
    width: 30,
    align: 'center',
    render: (row) => {
      if (!row.profile_img) {
        return h('span', { style: 'color: #ccc;' }, '-')
      }

      return h(
        'div',
        {
          style: 'position: relative; width: 50px; height: 50px;',
        },
        [
          h('img', {
            src: row.profile_img,
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
                  onClick: () => openPreview(row.profile_img, 'image'),
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
    key: 'profile_vid',
    width: 30,
    align: 'center',
    render: (row) => {
      const content = !row.profile_vid
        ? h(
            NButton,
            {
              size: 'tiny',
              type: 'primary',
              text: true,
              onClick: () => handleUploadVideo(row),
            },
            { icon: renderIcon('material-symbols:upload') },
          )
        : h(
            'div',
            {
              style: 'position: relative; width: 50px; height: 50px;',
            },
            [
              h('video', {
                src: row.profile_vid,
                style:
                  'width: 50px; height: 50px; object-fit: cover; border-radius: 4px; cursor: pointer;',
                muted: true,
                onMouseenter: (e) => e.target.play(),
                onMouseleave: (e) => {
                  e.target.pause()
                  e.target.currentTime = 0
                },
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
                      onClick: () => openPreview(row.profile_vid, 'video'),
                    },
                    { icon: renderIcon('material-symbols:visibility') },
                  ),
                  h(
                    NButton,
                    {
                      size: 'tiny',
                      type: 'primary',
                      text: true,
                      onClick: (e) => {
                        e.stopPropagation()
                        handleUploadVideo(row)
                      },
                    },
                    { icon: renderIcon('material-symbols:upload') },
                  ),
                ],
              ),
            ],
          )

      return h(NSpin, { show: modalLoading.value, style: 'display: inline-block;' }, () => content)
    },
  },
  {
    title: '头像',
    key: 'avatar',
    width: 30,
    align: 'center',
    render: (row) => {
      const content = !row.avatar
        ? h(
            NButton,
            {
              size: 'tiny',
              type: 'primary',
              text: true,
              onClick: () => handleUploadAvatar(row),
            },
            { icon: renderIcon('material-symbols:upload') },
          )
        : h(
            'div',
            {
              style: 'position: relative; width: 50px; height: 50px;',
            },
            [
              h('img', {
                src: row.avatar,
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
                      onClick: () => openPreview(row.avatar, 'image'),
                    },
                    { icon: renderIcon('material-symbols:visibility') },
                  ),
                  h(
                    NButton,
                    {
                      size: 'tiny',
                      type: 'primary',
                      text: true,
                      onClick: (e) => {
                        e.stopPropagation()
                        handleUploadAvatar(row)
                      },
                    },
                    { icon: renderIcon('material-symbols:upload') },
                  ),
                ],
              ),
            ],
          )

      return h(NSpin, { show: modalLoading.value, style: 'display: inline-block;' }, () => content)
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
            const res = await api.updateAgentTemplate({
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
    title: '功能描述',
    key: 'desc',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '排序',
    key: 'order',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '创建时间',
    key: 'create_at',
    width: 50,
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
          [[vPermission, 'post/api/v1/agent/template/update']],
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
                [[vPermission, 'delete/api/v1/agent/template/delete']],
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
  <CommonPage show-footer title="智能体模板列表">
    <template #action>
      <NButton v-permission="'post/api/v1/agent/template/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新增智能体模板
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getAgentTemplateList"
    >
      <template #queryBar>
        <QueryBarItem label="智能体模板名称" :label-width="100">
          <NInput
            v-model:value="queryItems.agent_name"
            clearable
            type="text"
            placeholder="请输入智能体模板名称"
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
        <div class="flex gap-16">
          <NFormItem
            label="模板名称"
            path="agent_name"
            :rule="{
              required: true,
              message: '请输入智能体模板名称',
              trigger: ['input', 'blur'],
            }"
          >
            <NInput
              v-model:value="modalForm.agent_name"
              placeholder="请输入智能体模板名称"
              maxlength="20"
              show-count
            />
          </NFormItem>
          <NFormItem
            label="助手名称"
            path="assistant_name"
            :rule="{
              required: true,
              message: '请输入助手名称',
              trigger: ['input', 'blur'],
            }"
          >
            <NInput
              v-model:value="modalForm.assistant_name"
              placeholder="请输入助手名称"
              maxlength="20"
              show-count
            />
          </NFormItem>
        </div>
        <NFormItem
          label="角色提示词"
          path="character"
          :rule="{
            required: true,
            message: '请输入角色提示词',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.character"
            type="textarea"
            :rows="4"
            clearable
            placeholder="请输入角色提示词"
            maxlength="1000"
            show-count
          />
        </NFormItem>
        <div class="flex gap-16">
          <NFormItem
            label="系统提示词"
            path="system_prompt"
            class="flex-1"
            :rule="{
              required: true,
              message: '请选择系统提示词',
              trigger: ['change', 'blur'],
            }"
          >
            <NSelect
              v-model:value="modalForm.system_prompt"
              :options="sysPromptList.map((item) => ({ label: item.name, value: item.content }))"
              placeholder="请选择系统提示词"
              clearable
            />
          </NFormItem>
          <NFormItem label="排序" path="order" class="flex-1">
            <NInputNumber
              v-model:value="modalForm.order"
              :min="0"
              placeholder="请输入排序值"
              clearable
            />
          </NFormItem>
        </div>
        <div class="flex gap-16">
          <NFormItem
            label="语言模型"
            path="llm_model"
            class="flex-1"
            :rule="{
              required: true,
              message: '请选择语言模型',
              trigger: ['change', 'blur'],
            }"
          >
            <NSelect
              v-model:value="modalForm.llm_model"
              :options="llmList.map((item) => ({ label: item.description, value: item.name }))"
              placeholder="请选择语言模型"
              clearable
            />
          </NFormItem>
          <NFormItem label="语音识别速度" path="asr_speed" class="flex-1">
            <NSelect
              v-model:value="modalForm.asr_speed"
              :options="asrSpeedOptions"
              placeholder="请选择语音识别速度"
              clearable
            />
          </NFormItem>
        </div>
        <div class="flex gap-16">
          <NFormItem
            label="对话语言"
            path="language"
            :rule="{
              required: true,
              message: '请选择对话语言',
              trigger: ['change', 'blur'],
            }"
            class="flex-1"
          >
            <NSelect
              v-model:value="modalForm.language"
              :options="languageOptions"
              placeholder="请选择对话语言"
              clearable
            />
          </NFormItem>
          <NFormItem
            label="角色音色"
            path="tts_voice"
            :rule="{
              required: true,
              message: '请选择角色音色',
              trigger: ['change', 'blur'],
            }"
            class="flex-1"
          >
            <NSelect
              v-model:value="modalForm.tts_voice"
              :options="filteredVoices"
              :render-label="renderVoiceLabel"
              placeholder="请先选择对话语言，再选择角色音色"
              clearable
            />
          </NFormItem>
        </div>
        <div class="flex gap-16">
          <NFormItem label="角色语速" path="tts_speech_speed" class="flex-1">
            <NSelect
              v-model:value="modalForm.tts_speech_speed"
              :options="ttsSpeedOptions"
              placeholder="请选择角色语速"
              clearable
            />
          </NFormItem>
          <NFormItem label="角色音调" path="tts_pitch" class="flex-1">
            <NInputNumber
              v-model:value="modalForm.tts_pitch"
              :min="-3"
              :max="3"
              placeholder="请输入角色音调(-3到3)"
              clearable
            />
          </NFormItem>
        </div>

        <div class="flex gap-16">
          <NFormItem
            label="角色形象"
            path="profile_id"
            class="flex-1"
            :rule="{
              type: 'number',
              required: true,
              message: '请选择角色形象',
              trigger: ['change', 'blur'],
            }"
          >
            <NSelect
              v-model:value="modalForm.profile_id"
              :options="profileOptions"
              placeholder="请选择角色形象"
              clearable
            />
          </NFormItem>
          <NFormItem label="形象照片" class="flex-1">
            <div class="w-50 h-50 rounded-lg border border-gray-200">
              <img
                v-if="currentProfileGenImg"
                :src="currentProfileGenImg"
                alt="形象照片"
                class="w-full h-full object-cover"
              />
            </div>
          </NFormItem>
        </div>

        <NFormItem label="功能描述" path="desc">
          <NInput
            v-model:value="modalForm.desc"
            type="text"
            clearable
            placeholder="请输入功能描述"
            maxlength="200"
            show-count
          />
        </NFormItem>
      </NForm>
    </CrudModal>

    <!-- 预览对话框 -->
    <NModal
      v-model:show="previewVisible"
      preset="card"
      style="width: 80%; max-width: 800px"
      :title="previewType === 'video' ? '预览视频' : '预览图片'"
    >
      <img
        v-if="previewType === 'image'"
        :src="previewUrl"
        alt="预览"
        style="width: 100%; height: auto; max-height: 70vh; object-fit: contain"
      />
      <video
        v-if="previewType === 'video'"
        :src="previewUrl"
        controls
        style="width: 100%; height: auto; max-height: 70vh"
      />
    </NModal>
  </CommonPage>
</template>
