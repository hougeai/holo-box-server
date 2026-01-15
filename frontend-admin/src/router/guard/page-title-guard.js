const baseTitle = import.meta.env.VITE_TITLE

export function createPageTitleGuard(router) {
  // 在路由跳转完成后执行
  router.afterEach((to) => {
    // 从路由的 meta 信息中获取页面标题，需要每个页面设置 meta.title
    const pageTitle = to.meta?.title
    if (pageTitle) {
      document.title = `${pageTitle} | ${baseTitle}`
    } else {
      document.title = baseTitle
    }
  })
}
