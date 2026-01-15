import { getToken, setToken } from '@/utils'
import { resolveResError } from './helpers'
import { useUserStore } from '@/store'
import api from '@/api'

// 请求成功拦截器
export function reqResolve(config) {
  // 处理不需要token的请求
  if (config.noNeedToken) {
    return config
  }
  // 这个token来自localStorage
  const token = getToken()
  if (token) {
    config.headers.token = config.headers.token || token
  }

  return config
}

//请求失败拦截器
export function reqReject(error) {
  return Promise.reject(error) // 直接抛出错误，传给前端的catch处理
}

// 响应成功拦截器
export function resResolve(response) {
  const { data, status, statusText } = response
  if (data?.code !== 200) {
    // ?? 运算符：当 data.code为 null 或 undefined 时，则返回status
    const code = data?.code ?? status
    /** 根据code处理对应的操作，并返回处理后的message */
    const message = resolveResError(code, data?.msg ?? statusText)
    window.$message?.error(message, { keepAliveOnHover: true })
    return Promise.reject({ code, message, error: data || response }) // catch时也会接收三个值
  }
  return Promise.resolve(data)
}

export function createInterceptors(service) {
  // 请求拦截器
  service.interceptors.request.use(reqResolve, reqReject)
  // 响应拦截器
  service.interceptors.response.use(resResolve, async function (error) {
    // 处理网络错误等
    if (!error || !error.response) {
      const code = error?.code
      /** 根据code处理对应的操作，并返回处理后的message */
      const message = resolveResError(code, error.message)
      window.$message?.error(message)
      return Promise.reject({ code, message, error })
    }
    const { data, status } = error.response
    // 处理419登录过期
    if (data?.code === 419) {
      try {
        const res = await api.refresh()
        setToken(res.data.access_token)
        // 重试之前失败的请求
        const config = error.response.config
        config.headers.token = res.data.access_token
        return service(config)
      } catch (error) {
        console.log('refresh token error', error)
        // refresh token 也失败了,执行登出
        const userStore = useUserStore()
        userStore.logout()
        return Promise.reject(error)
      }
    }
    // 处理401未授权
    if (data?.code === 401) {
      try {
        const userStore = useUserStore()
        userStore.logout()
      } catch (error) {
        console.log('resReject error', error)
        return
      }
    }
    // 后端返回的response数据
    const code = data?.code ?? status
    const message = resolveResError(code, data?.msg ?? error.message)
    window.$message?.error(message, { keepAliveOnHover: true })
    return Promise.reject({ code, message, error: error.response?.data || error.response })
  })
}
