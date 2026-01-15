export function createPageLoadingGuard(router) {
  // 路由跳转前：显示加载进度条
  router.beforeEach(() => {
    window.$loadingBar?.start()
  })
  // 路由跳转后：完成进度条
  router.afterEach(() => {
    setTimeout(() => {
      window.$loadingBar?.finish()
    }, 200)
  })
  // 路由错误：显示错误状态
  router.onError(() => {
    window.$loadingBar?.error()
  })
}
