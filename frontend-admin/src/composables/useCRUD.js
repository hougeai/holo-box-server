import { isNullOrWhitespace } from '@/utils'

const ACTIONS = {
  view: '查看',
  edit: '编辑',
  add: '新增',
}

export default function ({ name, initForm = {}, doCreate, doDelete, doUpdate, refresh }) {
  const modalVisible = ref(false) // 弹窗是否可见
  const modalAction = ref('') // 弹窗操作类型
  const modalTitle = computed(() => ACTIONS[modalAction.value] + name)
  const modalLoading = ref(false) // 表单提交loading
  const modalFormRef = ref(null) // 表单验证机制的关键连接点
  const modalForm = ref({ ...initForm }) // 表单数据

  /** 新增 */
  function handleAdd() {
    modalAction.value = 'add'
    modalVisible.value = true
    modalForm.value = { ...initForm }
  }

  /** 修改 */
  function handleEdit(row) {
    modalAction.value = 'edit'
    modalVisible.value = true
    modalForm.value = { ...row }
  }

  /** 查看 */
  function handleView(row) {
    modalAction.value = 'view'
    modalVisible.value = true
    modalForm.value = { ...row }
  }

  /** 保存 传入一些callback函数等待api成功调用后执行*/
  function handleSave(...callbacks) {
    if (!['edit', 'add'].includes(modalAction.value)) {
      modalVisible.value = false
      return
    }
    // modalFormRef 引用了 NForm 组件，接收 :rules="validateAddUser" 验证规则
    modalFormRef.value?.validate(async (err) => {
      if (err) return
      const actions = {
        add: {
          api: () => doCreate(modalForm.value),
          msg: () => $message.success('新增成功'),
        },
        edit: {
          api: () => doUpdate(modalForm.value),
          msg: () => $message.success('编辑成功'),
        },
      }
      const action = actions[modalAction.value]

      try {
        modalLoading.value = true
        for (const callback of callbacks) {
          const result = await callback()
          if (result === false) {
            modalLoading.value = false
            return
          }
        }
        console.log(modalForm.value)
        const data = await action.api()
        action.msg()
        modalLoading.value = modalVisible.value = false
        data && refresh(data)
      } catch (error) {
        console.log(error)
        modalLoading.value = false
      }
    })
  }

  /** 删除 */
  async function handleDelete(params = {}) {
    if (isNullOrWhitespace(params)) return
    try {
      modalLoading.value = true
      const data = await doDelete(params)
      $message.success('删除成功')
      modalLoading.value = false
      refresh(data)
    } catch (error) {
      console.log(error)
      modalLoading.value = false
    }
  }

  return {
    modalVisible,
    modalAction,
    modalTitle,
    modalLoading,
    handleAdd,
    handleDelete,
    handleEdit,
    handleView,
    handleSave,
    modalForm,
    modalFormRef,
  }
}
