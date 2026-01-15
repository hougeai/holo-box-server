import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router'
import { setupRouterGuard } from './guard'
import { basicRoutes, EMPTY_ROUTE, NOT_FOUND_ROUTE } from './routes'
import { getToken, isNullOrWhitespace } from '@/utils'
import { useUserStore, usePermissionStore } from '@/store'

const isHash = import.meta.env.VITE_USE_HASH === 'true'
export const router = createRouter({
  // 根据环境变量决定使用 hash 模式还是 history 模式
  history: isHash ? createWebHashHistory('/') : createWebHistory('/'),
  routes: basicRoutes, // 基础路由（不需要权限的路由，如登录页）
  scrollBehavior: () => ({ left: 0, top: 0 }), // 页面切换时滚动到顶部
})

export async function setupRouter(app) {
  await addDynamicRoutes() // 1. 添加动态路由
  setupRouterGuard(router) // 2. 设置路由守卫
  app.use(router) // 3. 注册路由到 Vue 应用实例中
}

export async function resetRouter() {
  // 获取基础路由名称
  const basicRouteNames = getRouteNames(basicRoutes)
  // 移除所有非基础路由
  router.getRoutes().forEach((route) => {
    const name = route.name
    if (!basicRouteNames.includes(name)) {
      router.removeRoute(name)
    }
  })
}

export async function addDynamicRoutes() {
  const token = getToken()
  // console.log('token', token)

  // 没有token情况：添加空路由（通常指向登录页）
  if (isNullOrWhitespace(token)) {
    router.addRoute(EMPTY_ROUTE)
    return
  }
  // 有token的情况
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()
  !userStore.userId && (await userStore.getUserInfo())
  try {
    // 获取用户的权限路由
    const accessRoutes = await permissionStore.generateRoutes()
    // console.log('accessRoutes', accessRoutes)
    // 获取用户的可访问 API
    await permissionStore.getAccessApis()
    // console.log('accessApis', permissionStore.accessApis)
    // 只添加用户有权限的路由
    accessRoutes.forEach((route) => {
      // 如果还不在路由表中，则添加
      !router.hasRoute(route.name) && router.addRoute(route)
    })
    // 移除空路由，添加 404 路由：没有token时添加的空路由，这时应该移除，添加 404 路由
    router.hasRoute(EMPTY_ROUTE.name) && router.removeRoute(EMPTY_ROUTE.name)
    router.addRoute(NOT_FOUND_ROUTE)
  } catch (error) {
    console.error('error', error)
    const userStore = useUserStore()
    await userStore.logout()
  }
}

export function getRouteNames(routes) {
  // flat的意思是把嵌套数组拉平，1代表只拉平一层，得到['dashboard', 'analysis', 'workplace', 'system', 'user']
  return routes.map((route) => getRouteName(route)).flat(1)
}

function getRouteName(route) {
  const names = [route.name]
  if (route.children && route.children.length) {
    names.push(...route.children.map((item) => getRouteName(item)).flat(1))
  }
  return names
}
