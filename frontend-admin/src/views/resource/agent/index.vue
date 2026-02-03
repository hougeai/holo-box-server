<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives, computed, watch } from 'vue'
import {
  NButton,
  NInput,
  NPopconfirm,
  NRadioGroup,
  NRadio,
  NSpace,
  NFormItem,
  NSelect,
} from 'naive-ui'

import { formatDateTime, renderIcon, languageMap, asrSpeedMap, ttsSpeedMap } from '@/utils'
import { useCRUD } from '@/composables'
import { useUserStore } from '@/store'
import api from '@/api'

defineOptions({ name: '智能体管理' })

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
  name: 'Agent',
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
    avatar: '',
    system_prompt: '',
    mcp_endpoints: [],
  },
  doCreate: api.createAgent,
  doUpdate: api.updateAgent,
  doDelete: api.deleteAgent,
  refresh: () => $table.value?.handleSearch(), // 在CrudTable中定义的
})

// LLM列表
const llmList = ref([])
// Voice列表
const voiceList = ref([])
// 形象列表
const profileList = ref([])
// MCP端点列表
const mcpList = ref([])

// AgentTemplate列表
const agentTemplateList = ref([])
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

// 获取MCP端点列表
const fetchMcpList = async () => {
  try {
    const res = await api.getMcpToolList({ public: true })
    if (res.data) {
      mcpList.value = res.data
    }
  } catch (error) {
    console.error('获取MCP端点列表失败:', error)
  }
}

// 获取AgentTemplate列表
const fetchAgentTemplateList = async () => {
  try {
    const res = await api.getAgentTemplateList({ public: true })
    if (res.data) {
      agentTemplateList.value = res.data
    }
  } catch (error) {
    console.error('获取AgentTemplate列表失败:', error)
  }
}

// 选择模板后填充表单
const handleSelectTemplate = (templateAgentId) => {
  const template = agentTemplateList.value.find((t) => t.agent_id === templateAgentId)
  if (template) {
    modalForm.value.agent_template_id = template.agent_id
    modalForm.value.agent_name = template.agent_name || ''
    modalForm.value.assistant_name = template.assistant_name || ''
    modalForm.value.character = template.character || ''
    modalForm.value.llm_model = template.llm_model || ''
    modalForm.value.language = template.language || ''
    modalForm.value.tts_voice = template.tts_voice || ''
    modalForm.value.tts_speech_speed = template.tts_speech_speed || 'normal'
    modalForm.value.asr_speed = template.asr_speed || 'normal'
    modalForm.value.tts_pitch = template.tts_pitch || 0
    modalForm.value.profile_id = template.profile_id || null
    modalForm.value.system_prompt = template.system_prompt || ''
  } else if (templateAgentId === null) {
    // 如果选择了"不使用模板"，重置表单为初始值
    modalForm.value.agent_template_id = null
    modalForm.value.agent_name = ''
    modalForm.value.assistant_name = '盒子'
    modalForm.value.character = ''
    modalForm.value.llm_model = 'xz-lite'
    modalForm.value.language = 'zh'
    modalForm.value.tts_voice = ''
    modalForm.value.tts_speech_speed = 'normal'
    modalForm.value.asr_speed = 'normal'
    modalForm.value.tts_pitch = 0
    modalForm.value.profile_id = null
    modalForm.value.system_prompt = ''
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

// 记忆类型选项
const memoryTypeOptions = [{ label: '短期记忆', value: 'SHORT_TERM' }]

// 形象选项
const profileOptions = computed(() => {
  return profileList.value.map((profile) => ({
    label: profile.name,
    value: Number(profile.id),
  }))
})

// MCP选项（用于下拉框）
const mcpOptions = computed(() => {
  return mcpList.value.map((mcp) => ({
    label: mcp.name,
    value: mcp.endpoint_id,
  }))
})

// 当前选中的profile对应的gen_img
const currentProfileGenImg = computed(() => {
  const profile = profileList.value.find((p) => p.id === modalForm.value.profile_id)
  return profile?.ori_img || ''
})

// 监听profile_id变化，同步更新avatar
watch(
  () => modalForm.value.profile_id,
  (newVal) => {
    const profile = profileList.value.find((p) => p.id === newVal)
    if (profile?.ori_img) {
      modalForm.value.avatar = profile.ori_img
    }
  },
  { immediate: true },
)

onMounted(async () => {
  $table.value?.handleSearch()
  await Promise.all([
    fetchLlmList(),
    fetchVoiceList(),
    fetchProfileList(),
    fetchMcpList(),
    fetchAgentTemplateList(),
  ])
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
    title: '智能体ID',
    key: 'agent_id',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '智能体名称',
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
    title: '头像',
    key: 'avatar',
    width: 30,
    align: 'center',
    render: (row) => {
      return row.avatar
        ? h('img', {
            src: row.avatar,
            style:
              'width: 50px; height: 50px; object-fit: cover; border-radius: 4px; cursor: pointer;',
            onClick: () => window.open(row.avatar, '_blank'),
          })
        : h('span', { style: 'color: #ccc;' }, '-')
    },
  },
  {
    title: '系统提示词',
    key: 'system_prompt',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'MCP端点',
    key: 'mcp_endpoints',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      const endpoints =
        typeof row.mcp_endpoints === 'string' ? JSON.parse(row.mcp_endpoints) : row.mcp_endpoints
      if (Array.isArray(endpoints) && endpoints.length > 0) {
        return endpoints.join(', ')
      }
      return '-'
    },
  },
  {
    title: '设备绑定量',
    key: 'device_count',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '来源',
    key: 'source',
    width: 30,
    align: 'center',
    ellipsis: { tooltip: true },
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
          [[vPermission, 'post/api/v1/agent/update']],
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
                [[vPermission, 'delete/api/v1/agent/delete']],
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
  <CommonPage show-footer title="智能体列表">
    <template #action>
      <NButton v-permission="'post/api/v1/agent/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新增智能体
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getAgentList"
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
        <QueryBarItem label="智能体ID" :label-width="60">
          <NInput
            v-model:value="queryItems.agent_id"
            clearable
            type="text"
            placeholder="请输入智能体ID"
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
        :disabled="modalAction === 'view'"
      >
        <NFormItem label="选择模板" v-if="agentTemplateList.length > 0">
          <NRadioGroup
            v-model:value="modalForm.agent_template_id"
            @update:value="handleSelectTemplate"
          >
            <NSpace horizontal>
              <NRadio :value="null">不使用模板</NRadio>
              <NRadio
                v-for="template in agentTemplateList"
                :key="template.agent_id"
                :value="template.agent_id"
              >
                {{ template.agent_name }}
              </NRadio>
            </NSpace>
          </NRadioGroup>
        </NFormItem>
        <NFormItem
          label="智能体名称"
          path="agent_name"
          :rule="{
            required: true,
            message: '请输入智能体名称',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.agent_name"
            placeholder="请输入智能体名称"
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
        <NFormItem
          label="语言模型"
          path="llm_model"
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
          <NFormItem label="语音识别速度" path="asr_speed" class="flex-1">
            <NSelect
              v-model:value="modalForm.asr_speed"
              :options="asrSpeedOptions"
              placeholder="请选择语音识别速度"
              clearable
            />
          </NFormItem>
          <NFormItem label="记忆类型" path="memory_type" class="flex-1">
            <NSelect
              v-model:value="modalForm.memory_type"
              :options="memoryTypeOptions"
              placeholder="请选择记忆类型"
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
          <NFormItem label="头像预览" class="flex-1">
            <div class="w-50 h-50 rounded-lg border border-gray-200">
              <img
                v-if="currentProfileGenImg"
                :src="currentProfileGenImg"
                alt="头像预览"
                class="w-full h-full object-cover"
              />
            </div>
          </NFormItem>
        </div>
        <NFormItem label="MCP工具" class="flex-1">
          <NSelect
            v-model:value="modalForm.mcp_endpoints"
            :options="mcpOptions"
            placeholder="请选择MCP工具（可多选）"
            multiple
            clearable
            filterable
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
