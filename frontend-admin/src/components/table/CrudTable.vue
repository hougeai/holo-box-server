<template>
  <div v-bind="$attrs">
    <!-- 查询栏部分 -->
    <QueryBar v-if="$slots.queryBar" mb-30 @search="handleSearch" @reset="handleReset">
      <slot name="queryBar" />
      <!-- 插槽：允许父组件定制查询条件 -->
    </QueryBar>
    <!-- 数据表格部分 -->
    <n-data-table
      :remote="remote"
      :loading="loading"
      :columns="columns"
      :data="tableData"
      :scroll-x="scrollX"
      :row-key="(row) => row[rowKey]"
      :pagination="isPagination ? pagination : false"
      @update:checked-row-keys="onChecked"
      @update:page="onPageChange"
    />
  </div>
</template>

<script setup>
// props内的字段可以从父组件传入
const props = defineProps({
  // 是否使用后端分页 true: 后端分页  false： 前端分页
  remote: {
    type: Boolean,
    default: true,
  },
  // 是否分页
  isPagination: {
    type: Boolean,
    default: true,
  },
  scrollX: {
    type: Number,
    default: 450,
  },
  rowKey: {
    type: String,
    default: 'id',
  },
  columns: {
    type: Array,
    required: true,
  },
  /** queryBar中的参数：查询条件 */
  queryItems: {
    type: Object,
    default() {
      return {}
    },
  },
  /** 补充参数（可选） */
  extraParams: {
    type: Object,
    default() {
      return {}
    },
  },
  /**
   * ! 约定接口入参出参
   * * 分页模式需约定分页接口入参
   *    @page_size 分页参数：一页展示多少条，默认10
   *    @page   分页参数：页码，默认1
   */
  // 获取数据的方法
  getData: {
    type: Function,
    required: true,
  },
})
// emits内的字段可以触发外部事件，供父组件调用
const emit = defineEmits(['update:queryItems', 'onChecked', 'onDataChange'])
const loading = ref(false)
const initQuery = { ...props.queryItems }
const tableData = ref([])
// 分页配置
const pagination = reactive({
  page: 1,
  page_size: 10,
  pageSizes: [10, 20, 50, 100],
  showSizePicker: true,
  // { itemCount } 使用了 ES6 的解构赋值语法，函数接收一个对象参数，这个对象包含了 itemCount 属性
  prefix({ itemCount }) {
    return `共 ${itemCount} 条`
  },
  onChange: (page) => {
    pagination.page = page
  },
  onUpdatePageSize: (pageSize) => {
    pagination.page_size = pageSize
    pagination.page = 1
    handleQuery()
  },
})
// 核心方法，负责数据获取
async function handleQuery() {
  try {
    loading.value = true
    let paginationParams = {}
    // 如果非分页模式或者使用前端分页,则无需传分页参数
    if (props.isPagination && props.remote) {
      paginationParams = { page: pagination.page, page_size: pagination.page_size }
    }
    const { data, total } = await props.getData({
      ...props.queryItems,
      ...props.extraParams,
      ...paginationParams,
    })
    tableData.value = data
    pagination.itemCount = total || 0
  } catch (error) {
    console.error(error)
    tableData.value = []
    pagination.itemCount = 0
  } finally {
    emit('onDataChange', tableData.value)
    loading.value = false
  }
}
//搜索：重置页码并查询
function handleSearch() {
  pagination.page = 1
  handleQuery()
}
// 重置查询条件
async function handleReset() {
  const queryItems = { ...props.queryItems }
  for (const key in queryItems) {
    queryItems[key] = null
  }
  emit('update:queryItems', { ...queryItems, ...initQuery })
  await nextTick() // 确保 Vue 的 DOM 更新完成后再执行后续代码。
  pagination.page = 1
  handleQuery()
}
function onPageChange(currentPage) {
  pagination.page = currentPage
  if (props.remote) {
    handleQuery()
  }
}
function onChecked(rowKeys) {
  if (props.columns.some((item) => item.type === 'selection')) {
    emit('onChecked', rowKeys)
  }
}

defineExpose({
  handleSearch, // 用于父组件搜索
  handleReset, // 用于父组件重置查询条件
  tableData, // 用于父组件获取数据
})
</script>
