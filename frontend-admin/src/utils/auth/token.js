import { lStorage } from '@/utils'

export function getToken() {
  return lStorage.get('access_token')
}

export function setToken(token) {
  lStorage.set('access_token', token)
}

export function removeToken() {
  lStorage.remove('access_token')
}
