import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite' // 自动导入 Vue、Vue Router 等 API
import Components from 'unplugin-vue-components/vite' // 自动引入组件
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'
import { FileSystemIconLoader } from 'unplugin-icons/loaders'
import IconsResolver from 'unplugin-icons/resolver'

/**
 * * unplugin-icons插件，自动引入iconify图标
 * usage: https://github.com/antfu/unplugin-icons
 * 图标库: https://icones.js.org/
 */
import Icons from 'unplugin-icons/vite'
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons' // SVG 图标处理插件，用于处理自定义 SVG 图标

import { getSrcPath } from '../utils'

const customIconPath = resolve(getSrcPath(), 'assets/svg')

export default [
  AutoImport({
    imports: ['vue', 'vue-router'],
    dts: false, // 不生成.d.ts 文件-TypeScript 声明文件，使用 TypeScript 时有用
  }),
  Icons({
    compiler: 'vue3',
    customCollections: {
      custom: FileSystemIconLoader(customIconPath), // 配置自定义图标路径，和 集合
    },
    scale: 1, // 图标缩放比例
    defaultClass: 'inline-block', // 添加默认 css 类
  }),
  Components({
    resolvers: [
      NaiveUiResolver(), // 自动导入Naive UI组件
      IconsResolver({ customCollections: ['custom'], componentPrefix: 'icon' }),
    ], // 有了这个插件 icon-custom-logo 就能引入assets/svg/logo.svg 图标，只能处理.svg文件，支持动态修改图标样式（颜色、大小等）
    dts: false,
    dirs: ['src/components'], //自动导入目录下的组件，比如有 MyButton.vue ，可以直接使用 <my-button>
  }),
  createSvgIconsPlugin({
    // 以 SVG Sprite 方式使用图标
    iconDirs: [customIconPath],
    symbolId: 'icon-custom-[dir]-[name]',
    inject: 'body-last', // 注入位置
    customDomId: '__CUSTOM_SVG_ICON__',
  }),
]
