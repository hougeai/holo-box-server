import { defineConfig, loadEnv } from 'vite'

import { convertEnv, getSrcPath, getRootPath } from './build/utils'
import { viteDefine } from './build/config'
import { createVitePlugins } from './build/plugin'

export default defineConfig(({ command, mode }) => {
  const srcPath = getSrcPath()
  const rootPath = getRootPath()
  const isBuild = command === 'build'

  const env = loadEnv(mode, process.cwd()) // 返回所有符合当前模式的.env文件
  const viteEnv = convertEnv(env)
  const { VITE_PORT, VITE_PUBLIC_PATH, VITE_USE_PROXY, VITE_BASE_API, VITE_BASE_API_URL } = viteEnv

  return {
    base: VITE_PUBLIC_PATH || '/',
    resolve: {
      alias: {
        '~': rootPath,
        '@': srcPath,
      },
    },
    define: viteDefine,
    plugins: createVitePlugins(viteEnv, isBuild), // 所有插件入口
    server: {
      // server就是开发环境配置
      host: '0.0.0.0',
      port: VITE_PORT,
      open: true,
      proxy: VITE_USE_PROXY
        ? {
            [VITE_BASE_API]: {
              target: VITE_BASE_API_URL,
              changeOrigin: true,
            },
          }
        : undefined,
    },
    build: {
      target: 'es2015', // 对于旧版本的浏览器，建议使用 es2015，Vite 的默认 target 是 'modules'
      outDir: 'dist',
      reportCompressedSize: false, // 启用/禁用 gzip 压缩大小报告
      chunkSizeWarningLimit: 1024, // chunk 大小警告的限制（单位kb）
    },
  }
})
