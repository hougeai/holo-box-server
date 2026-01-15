<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NPopconfirm,
  NTag,
  NTree,
  NDrawer,
  NDrawerContent,
  NTabs,
  NTabPane,
  NGrid,
  NGi,
  NInputNumber,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '角色管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const {
  modalVisible,
  modalAction,
  modalTitle,
  modalLoading,
  handleAdd,
  handleDelete,
  handleEdit,
  handleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: '角色',
  initForm: {},
  doCreate: api.createRole,
  doDelete: api.deleteRole,
  doUpdate: api.updateRole,
  refresh: () => $table.value?.handleSearch(),
})

const pattern = ref('')
const menuOption = ref([]) // 菜单选项
const active = ref(false)
const menu_ids = ref([])
const role_id = ref(0)
const apiOption = ref([])
const api_ids = ref([])
const apiTree = ref([])

function buildApiTree(data) {
  const processedData = []
  const groupedData = {}

  data.forEach((item) => {
    const tags = item['tags']
    const pathParts = item['path'].split('/')
    const path = pathParts.slice(0, -1).join('/')
    const summary = tags.charAt(0).toUpperCase() + tags.slice(1)
    const unique_id = item['method'].toLowerCase() + item['path']
    if (!(path in groupedData)) {
      groupedData[path] = { unique_id: path, path: path, summary: summary, children: [] }
    }

    groupedData[path].children.push({
      id: item['id'],
      path: item['path'],
      method: item['method'],
      summary: item['summary'],
      unique_id: unique_id,
    })
  })
  processedData.push(...Object.values(groupedData))
  return processedData
}

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
    title: '角色名',
    key: 'name',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(NTag, { type: 'info' }, { default: () => row.name })
    },
  },
  {
    title: '角色描述',
    key: 'desc',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '创建日期',
    key: 'created_at',
    width: 40,
    align: 'center',
    render(row) {
      return h('span', formatDate(row.created_at))
    },
  },
  {
    title: '配额信息',
    key: 'quota',
    width: 40,
    align: 'center',
    render(row) {
      return h('div', [
        h('div', `设备: ${row.max_devices}`),
        h('div', `闹钟: ${row.max_alarms}`),
        h('div', `播放: ${row.max_dailyplay}/日`),
        h('div', `歌单: ${row.max_playlist}`),
        h('div', `上传: ${row.max_upload_songs}`),
        h('div', `API: ${row.max_apikeys}`),
        h('div', `文件: ${row.kb_file_quota}`),
        h('div', `向量: ${row.kb_storage_quota}`),
        h('div', `Dify: ${row.kb_dify_limit}`),
        h('div', `MCP服务: ${row.max_mcp}`),
        h('div', `MCP绑定: ${row.max_mcp_bind}`),
      ])
    },
  },
  {
    title: '价格信息',
    key: 'price',
    width: 40,
    align: 'center',
    render(row) {
      return h('div', [
        h('div', `月付: ¥${row.price_monthly}`),
        h('div', `年付: ¥${row.price_yearly}`),
      ])
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
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
              icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
            },
          ),
          [[vPermission, 'post/api/v1/role/update']],
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ role_id: row.id }, false),
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
                [[vPermission, 'delete/api/v1/role/delete']],
              ),
            default: () => h('div', {}, '确定删除该角色吗?'),
          },
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              onClick: async () => {
                try {
                  // 使用 Promise.all 来并行发送所有请求，要么全部成功，要么全部失败（如果其中一个失败，整个 Promise.all 会 reject）
                  const [menusResponse, apisResponse, roleAuthorizedResponse] = await Promise.all([
                    api.getMenus({ page: 1, page_size: 9999 }),
                    api.getApis({ page: 1, page_size: 9999 }),
                    api.getRoleAuthorized({ id: row.id }),
                  ])

                  // 处理每个请求的响应
                  menuOption.value = menusResponse.data
                  apiOption.value = buildApiTree(apisResponse.data)
                  menu_ids.value = roleAuthorizedResponse.data.menus.map((v) => v.id)
                  api_ids.value = roleAuthorizedResponse.data.apis.map(
                    (v) => v.method.toLowerCase() + v.path,
                  )

                  active.value = true
                  role_id.value = row.id
                } catch (error) {
                  // 错误处理
                  console.error('Error loading data:', error)
                }
              },
            },
            {
              default: () => '设置权限',
              icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
            },
          ),
          [[vPermission, 'get/api/v1/role/authorized']],
        ),
      ]
    },
  },
]

async function updateRoleAuthorized() {
  const checkData = apiTree.value.getCheckedData()
  const apiInfos = []
  checkData &&
    checkData.options.forEach((item) => {
      if (!item.children) {
        apiInfos.push({
          path: item.path,
          method: item.method,
        })
      }
    })
  const { code, msg } = await api.updateRoleAuthorized({
    id: role_id.value,
    menu_ids: menu_ids.value,
    api_infos: apiInfos,
  })
  if (code === 200) {
    $message?.success('设置成功')
  } else {
    $message?.error(msg)
  }

  const result = await api.getRoleAuthorized({ id: role_id.value })
  menu_ids.value = result.data.menus.map((v) => {
    return v.id
  })
}
</script>

<template>
  <CommonPage show-footer title="角色列表">
    <template #action>
      <NButton v-permission="'post/api/v1/role/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建角色
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRoleList"
    >
      <template #queryBar>
        <QueryBarItem label="角色名" :label-width="50">
          <NInput
            v-model:value="queryItems.role_name"
            clearable
            type="text"
            placeholder="请输入角色名"
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
        <NFormItem
          label="角色名"
          path="name"
          :rule="{
            required: true,
            message: '请输入角色名称',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput v-model:value="modalForm.name" placeholder="请输入角色名称" />
        </NFormItem>
        <NFormItem label="角色描述" path="desc">
          <NInput v-model:value="modalForm.desc" placeholder="请输入角色描述" />
        </NFormItem>
        <!-- 配额设置 -->
        <NFormItem label="最大设备数" path="max_devices">
          <NInputNumber
            v-model:value="modalForm.max_devices"
            placeholder="请输入最大设备绑定数量"
          />
        </NFormItem>
        <NFormItem label="最大闹钟数" path="max_alarms">
          <NInputNumber v-model:value="modalForm.max_alarms" placeholder="请输入最大闹钟设置数量" />
        </NFormItem>
        <NFormItem label="每日播放次数" path="max_dailyplay">
          <NInputNumber
            v-model:value="modalForm.max_dailyplay"
            placeholder="请输入每日音乐播放次数限制"
          />
        </NFormItem>
        <NFormItem label="歌单最大歌曲数" path="max_playlist">
          <NInputNumber
            v-model:value="modalForm.max_playlist"
            placeholder="请输入歌单最大歌曲数量"
          />
        </NFormItem>
        <NFormItem label="最大上传歌曲数" path="max_upload_songs">
          <NInputNumber
            v-model:value="modalForm.max_upload_songs"
            placeholder="请输入最大上传歌曲数量"
          />
        </NFormItem>
        <NFormItem label="最大API密钥数" path="max_apikeys">
          <NInputNumber v-model:value="modalForm.max_apikeys" placeholder="请输入最大API密钥数量" />
        </NFormItem>
        <NFormItem label="文件存储额度" path="kb_file_quota">
          <NInputNumber v-model:value="modalForm.kb_file_quota" placeholder="请输入文件存储额度" />
        </NFormItem>
        <NFormItem label="向量存储额度" path="kb_storage_quota">
          <NInputNumber
            v-model:value="modalForm.kb_storage_quota"
            placeholder="请输入向量存储额度"
          />
        </NFormItem>
        <NFormItem label="Dify知识库" path="kb_dify_limit">
          <NInputNumber
            v-model:value="modalForm.kb_dify_limit"
            placeholder="请输入Dify知识库数量限制"
          />
        </NFormItem>
        <NFormItem label="MCP服务" path="max_mcp">
          <NInputNumber v-model:value="modalForm.max_mcp" placeholder="请输入MCP服务数量限制" />
        </NFormItem>
        <NFormItem label="MCP绑定" path="max_mcp_bind">
          <NInputNumber
            v-model:value="modalForm.max_mcp_bind"
            placeholder="请输入MCP绑定数量限制"
          />
        </NFormItem>

        <!-- 价格设置 -->
        <NFormItem label="月付价格" path="price_monthly">
          <NInputNumber v-model:value="modalForm.price_monthly" placeholder="请输入月付价格" />
        </NFormItem>
        <NFormItem label="年付价格" path="price_yearly">
          <NInputNumber v-model:value="modalForm.price_yearly" placeholder="请输入年付价格" />
        </NFormItem>
      </NForm>
    </CrudModal>

    <NDrawer v-model:show="active" placement="right" :width="500"
      ><NDrawerContent>
        <NGrid x-gap="24" cols="12">
          <NGi span="8">
            <NInput
              v-model:value="pattern"
              type="text"
              placeholder="筛选"
              style="flex-grow: 1"
            ></NInput>
          </NGi>
          <NGi offset="2">
            <NButton
              v-permission="'post/api/v1/role/authorized'"
              type="info"
              @click="updateRoleAuthorized"
              >确定</NButton
            >
          </NGi>
        </NGrid>
        <NTabs>
          <NTabPane name="menu" tab="菜单权限" display-directive="show">
            <!-- TODO：级联 -->
            <NTree
              :data="menuOption"
              :checked-keys="menu_ids"
              :pattern="pattern"
              :show-irrelevant-nodes="false"
              key-field="id"
              label-field="name"
              checkable
              :default-expand-all="true"
              :block-line="true"
              :selectable="false"
              @update:checked-keys="(v) => (menu_ids = v)"
            />
          </NTabPane>
          <NTabPane name="resource" tab="接口权限" display-directive="show">
            <NTree
              ref="apiTree"
              :data="apiOption"
              :checked-keys="api_ids"
              :pattern="pattern"
              :show-irrelevant-nodes="false"
              key-field="unique_id"
              label-field="summary"
              checkable
              :default-expand-all="true"
              :block-line="true"
              :selectable="false"
              cascade
              @update:checked-keys="(v) => (api_ids = v)"
            />
          </NTabPane>
        </NTabs>
        <template #header> 设置权限 </template>
      </NDrawerContent>
    </NDrawer>
  </CommonPage>
</template>
