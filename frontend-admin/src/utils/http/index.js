import axios from 'axios'
import { createInterceptors } from './interceptors'

export function createAxios(options = {}) {
  const defaultOptions = {
    timeout: 12000,
    withCredentials: true, // 携带当前域名的cookie
    transformRequest: [
      function (data, headers) {
        if (data instanceof FormData) {
          // 对于 FormData，让浏览器自动处理 Content-Type
          delete headers['Content-Type']
          return data
        }
        if (typeof data === 'object') {
          headers['Content-Type'] = 'application/json'
          return JSON.stringify(data)
        }
        return data
      },
    ],
  }
  const service = axios.create({
    ...defaultOptions,
    ...options,
  })
  // 添加请求和响应拦截器
  createInterceptors(service)
  return service
}

export const request = createAxios({
  baseURL: import.meta.env.VITE_BASE_API,
})
