import { defineStore } from 'pinia'
import { activeTag, tags, WITHOUT_TAG_PATHS } from './helpers'
import { router } from '@/router'
import { lStorage } from '@/utils'

export const useTagsStore = defineStore('tag', {
  state() {
    return {
      tags: tags || [],
      activeTag: activeTag || '',
    }
  },
  getters: {
    activeIndex() {
      return this.tags.findIndex((item) => item.path === this.activeTag)
    },
  },
  actions: {
    setActiveTag(path) {
      this.activeTag = path
      lStorage.set('activeTag', path)
    },
    setTags(tags) {
      this.tags = tags
      lStorage.set('tags', tags)
    },
    addTag(tag = {}) {
      this.setActiveTag(tag.path)
      if (WITHOUT_TAG_PATHS.includes(tag.path) || this.tags.some((item) => item.path === tag.path))
        return
      this.setTags([...this.tags, tag])
    },

    removeTag(path) {
      // 如果关闭的是当前激活的标签
      if (path === this.activeTag) {
        if (this.activeIndex > 0) {
          // 如果不是第一个标签，则切换到左侧标签
          router.push(this.tags[this.activeIndex - 1].path)
        } else {
          // 如果是第一个标签，则切换到右侧标签
          router.push(this.tags[this.activeIndex + 1].path)
        }
      }
      // 从标签列表中移除该标签，即便是非激活的标签
      this.setTags(this.tags.filter((tag) => tag.path !== path))
    },
    removeOther(curPath = this.activeTag) {
      // 只保留 curPath 对应的标签，过滤掉其他所有标签
      this.setTags(this.tags.filter((tag) => tag.path === curPath))
      if (curPath !== this.activeTag) {
        router.push(this.tags[this.tags.length - 1].path)
      }
    },
    removeLeft(curPath) {
      const curIndex = this.tags.findIndex((item) => item.path === curPath)
      const filterTags = this.tags.filter((item, index) => index >= curIndex)
      this.setTags(filterTags)
      if (!filterTags.find((item) => item.path === this.activeTag)) {
        router.push(filterTags[filterTags.length - 1].path)
      }
    },
    removeRight(curPath) {
      const curIndex = this.tags.findIndex((item) => item.path === curPath)
      const filterTags = this.tags.filter((item, index) => index <= curIndex)
      this.setTags(filterTags)
      if (!filterTags.find((item) => item.path === this.activeTag)) {
        router.push(filterTags[filterTags.length - 1].path)
      }
    },
    resetTags() {
      this.setTags([])
      this.setActiveTag('')
    },
  },
})
