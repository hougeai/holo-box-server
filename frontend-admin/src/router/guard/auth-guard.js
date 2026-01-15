import { getToken, isNullOrWhitespace } from '@/utils'

const WHITE_LIST = ['/login', '/404']
export function createAuthGuard(router) {
  router.beforeEach(async (to) => {
    const token = getToken()

    /** 没有token的情况 */
    if (isNullOrWhitespace(token)) {
      // 如果访问的是白名单页面（登录页或404），允许访问
      if (WHITE_LIST.includes(to.path)) return true
      // 否则重定向到登录页，并记录原目标路径
      return { path: '/login', query: { ...to.query, redirect: to.path } }
    }

    /** 有token的情况 */
    if (to.path === '/login') return { path: '/' } // 已登录时访问登录页，重定向到首页
    return true // 其他情况允许访问
  })
}
