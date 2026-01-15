<template>
  <ScrollX ref="scrollXRef" class="bg-white dark:bg-dark!">
    <n-tag
      v-for="tag in tagsStore.tags"
      ref="tabRefs"
      :key="tag.path"
      class="mx-5 cursor-pointer rounded-4 px-15 hover:color-primary"
      :type="tagsStore.activeTag === tag.path ? 'primary' : 'default'"
      :closable="tagsStore.tags.length > 1"
      @click="handleTagClick(tag.path)"
      @close.stop="tagsStore.removeTag(tag.path)"
      @contextmenu.prevent="handleContextMenu($event, tag)"
    >
      {{ tag.title }}
    </n-tag>
    <ContextMenu
      v-if="contextMenuOption.show"
      v-model:show="contextMenuOption.show"
      :current-path="contextMenuOption.currentPath"
      :x="contextMenuOption.x"
      :y="contextMenuOption.y"
    />
  </ScrollX>
</template>

<script setup>
import ContextMenu from './ContextMenu.vue'
import { useTagsStore } from '@/store'
import ScrollX from '@/components/common/ScrollX.vue'

const route = useRoute()
const router = useRouter()
const tagsStore = useTagsStore()
const tabRefs = ref([])
const scrollXRef = ref(null)

const contextMenuOption = reactive({
  show: false,
  x: 0,
  y: 0,
  currentPath: '',
})
// 监听路由变化：当路由变化时，自动添加新的标签页
watch(
  () => route.path,
  () => {
    const { name, fullPath: path } = route
    const title = route.meta?.title
    tagsStore.addTag({ name, path, title })
  },
  { immediate: true }, // 表示组件创建时就执行一次
)
// 监听活动标签的索引：当切换标签时触发，计算新标签的位置，调用 ScrollX 组件的方法滚动到该位置
watch(
  () => tagsStore.activeIndex,
  async (activeIndex) => {
    // 当活动标签改变时，自动滚动到该标签的位置
    await nextTick()
    const activeTabElement = tabRefs.value[activeIndex]?.$el
    if (!activeTabElement) return
    const { offsetLeft: x, offsetWidth: width } = activeTabElement
    scrollXRef.value?.handleScroll(x + width, width)
  },
  { immediate: true },
)

const handleTagClick = (path) => {
  tagsStore.setActiveTag(path)
  router.push(path)
}

function showContextMenu() {
  contextMenuOption.show = true
}
function hideContextMenu() {
  contextMenuOption.show = false
}
function setContextMenu(x, y, currentPath) {
  Object.assign(contextMenuOption, { x, y, currentPath })
}

// 右击菜单
async function handleContextMenu(e, tagItem) {
  const { clientX, clientY } = e
  hideContextMenu()
  setContextMenu(clientX, clientY, tagItem.path)
  await nextTick()
  showContextMenu()
}
</script>

<style>
.n-tag__close {
  box-sizing: content-box;
  border-radius: 50%;
  font-size: 12px;
  padding: 2px;
  transform: scale(0.9);
  transform: translateX(5px);
  transition: all 0.3s;
}
</style>
