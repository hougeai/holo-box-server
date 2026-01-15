import vue from '@vitejs/plugin-vue' // Vue 官方插件，用于处理 .vue 单文件组件

/**
 * * unocss插件，原子css
 * https://github.com/antfu/unocss
 */
import Unocss from 'unocss/vite' // 原子化 CSS 引擎

// rollup打包分析插件
import { visualizer } from 'rollup-plugin-visualizer'
// 压缩
import viteCompression from 'vite-plugin-compression'

import { configHtmlPlugin } from './html' // HTML 处理插件，用于注入变量到 HTML 模板中，如网站标题等
import unplugin from './unplugin'

export function createVitePlugins(viteEnv, isBuild) {
  const plugins = [vue(), ...unplugin, configHtmlPlugin(viteEnv, isBuild), Unocss()]

  if (viteEnv.VITE_USE_COMPRESS) {
    plugins.push(viteCompression({ algorithm: viteEnv.VITE_COMPRESS_TYPE || 'gzip' }))
  }

  if (isBuild) {
    plugins.push(
      visualizer({
        open: true,
        gzipSize: true,
        brotliSize: true,
      }),
    )
  }

  return plugins
}
