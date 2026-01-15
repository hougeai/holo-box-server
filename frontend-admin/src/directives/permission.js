import { useUserStore, usePermissionStore } from '@/store'

function hasPermission(permission) {
  const userStore = useUserStore()
  const userPermissionStore = usePermissionStore()

  const accessApis = userPermissionStore.apis
  // 如果是超级用户，直接返回 true
  if (userStore.isSuperUser) {
    return true
  }
  // 否则检查是否有该 API 权限
  return accessApis.includes(permission)
}

export default function setupPermissionDirective(app) {
  function updateElVisible(el, permission) {
    if (!permission) {
      // throw 会中断当前执行流程，阻止后续代码执行
      throw new Error(`need roles: like v-permission="get/api/v1/user/list"`)
    }
    // 如果没有权限，直接从 DOM 中移除该元素
    if (!hasPermission(permission)) {
      el.parentElement?.removeChild(el)
    }
  }

  const permissionDirective = {
    // 元素首次渲染时
    mounted(el, binding) {
      updateElVisible(el, binding.value)
    },
    // 元素更新时
    beforeUpdate(el, binding) {
      updateElVisible(el, binding.value)
    },
  }

  app.directive('permission', permissionDirective)
}
