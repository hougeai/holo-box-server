import { defineStore } from 'pinia'
import { resetRouter } from '@/router'
import { useTagsStore, usePermissionStore } from '@/store'
import { removeToken, toLogin } from '@/utils'
import api from '@/api'
import defaultAvatar from '@/assets/images/default-avatar.webp'

export const useUserStore = defineStore('user', {
  state() {
    return {
      userInfo: {},
    }
  },
  // getters直接返回属性，直接用userStore.name而不需要userStore.userInfo.username
  getters: {
    userId() {
      return this.userInfo?.user_id
    },
    name() {
      return this.userInfo?.user_name
    },
    email() {
      return this.userInfo?.email
    },
    avatar() {
      return this.userInfo?.avatar || defaultAvatar
    },
    role_id() {
      return this.userInfo?.role_id || 0
    },
    isActive() {
      return this.userInfo?.is_active
    },
  },
  actions: {
    async getUserInfo() {
      try {
        const res = await api.getUserInfo()
        if (res.code === 401) {
          this.logout()
          return
        }
        // console.log(res.data)
        const { user_id, user_name, email, avatar, role_id, is_active } = res.data
        this.userInfo = { user_id, user_name, email, avatar, role_id, is_active }
        return res.data
      } catch (error) {
        return error
      }
    },
    async logout() {
      // 1. 清理标签页
      // 2. 清理权限信息
      // 3. 移除 token
      // 4. 重置路由
      // 5. 重置用户状态
      // 6. 跳转到登录页
      const { resetTags } = useTagsStore()
      const { resetPermission } = usePermissionStore()
      removeToken()
      resetTags()
      resetPermission()
      resetRouter()
      this.$reset()
      toLogin()
    },
    setUserInfo(userInfo = {}) {
      // 保留原对象中未更新的字段，新对象中的值覆盖同名字段，避免手动指定要保留的字段
      this.userInfo = { ...this.userInfo, ...userInfo }
    },
  },
})
