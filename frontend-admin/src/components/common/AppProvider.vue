<template>
  <n-config-provider
    wh-full
    :locale="zhCN"
    :date-locale="dateZhCN"
    :theme="appStore.isDark ? darkTheme : undefined"
    :theme-overrides="naiveThemeOverrides"
  >
    <n-loading-bar-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-message-provider>
            <slot></slot>
            <NaiveProviderContent />
          </n-message-provider>
        </n-notification-provider>
      </n-dialog-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup>
import { defineComponent, h } from 'vue'
import {
  zhCN,
  dateZhCN,
  darkTheme,
  useLoadingBar,
  useDialog,
  useMessage,
  useNotification,
} from 'naive-ui'
import { useCssVar } from '@vueuse/core'
import { kebabCase } from 'lodash-es' // kebabCase函数用于将驼峰式字符串转换为短横线连接，CSS 变量名通常使用短横线命名法
import { setupMessage, setupDialog } from '@/utils'
import { naiveThemeOverrides } from '~/settings'
import { useAppStore } from '@/store'

const appStore = useAppStore()

// 将主题配置转换为 CSS 变量应用到根元素
function setupCssVar() {
  const common = naiveThemeOverrides.common
  for (const key in common) {
    // 遍历主题配置，转换为 CSS 变量
    // 例如：primaryColor -> --primary-color
    useCssVar(`--${kebabCase(key)}`, document.documentElement).value = common[key] || ''
    if (key === 'primaryColor') window.localStorage.setItem('__THEME_COLOR__', common[key] || '')
  }
}

// 挂载naive组件的方法至window, 以便在全局使用，window 对象是全局作用域，代表了浏览器窗口
function setupNaiveTools() {
  window.$loadingBar = useLoadingBar()
  window.$notification = useNotification()

  window.$message = setupMessage(useMessage())
  window.$dialog = setupDialog(useDialog())
}

// 隐藏组件，用于执行初始化逻辑
const NaiveProviderContent = defineComponent({
  setup() {
    setupCssVar()
    setupNaiveTools()
  },
  render() {
    return h('div')
  },
})
</script>
