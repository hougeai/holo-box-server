import { lStorage } from '@/utils'
// 从本地存储获取当前激活的标签和所有标签
export const activeTag = lStorage.get('activeTag')
export const tags = lStorage.get('tags')
// 定义不需要显示在标签页中的路径
export const WITHOUT_TAG_PATHS = ['/404', '/login']
