/** 重置样式 */
import '@/styles/reset.css' // 重置默认样式
import 'uno.css'
import '@/styles/global.scss' // 全局样式

import { createApp } from 'vue'
import { setupRouter } from '@/router'
import { setupStore } from '@/store'
import App from './App.vue'
import { setupDirectives } from '@/directives' // 自定义指令
import { useResize } from '@/utils/common'
import i18n from '~/i18n'

async function setupApp() {
  // 1. 创建 Vue 应用实例
  const app = createApp(App)
  // 2. 初始化状态管理
  setupStore(app)
  // 3. 初始化路由（异步，可能需要处理权限等）
  await setupRouter(app)
  // 4. 注册自定义指令 - v-permission ，用于权限控制
  setupDirectives(app)
  // 5. 注册 resize 事件
  app.use(useResize)
  // 6. 注册国际化插件
  app.use(i18n)
  // 7. 挂载应用
  app.mount('#app')
}

setupApp()
