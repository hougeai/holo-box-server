// 所有的 HTTP 请求都通过一个统一的 request 实例处理
import { request } from '@/utils'

export default {
  // 用户认证相关
  login: (data) => request.post('/base/access_token', data),
  refresh: () => request.post('/base/refresh_token'),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // system-user
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete('/user/delete', { params }),
  resetPassword: (data = {}) => request.post('/user/reset_password', data),
  // system-role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // system-auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),
  // resource-agent
  getAgentList: (params = {}) => request.get('/agent/list', { params }),
  createAgent: (data = {}) => request.post('/agent/create', data),
  updateAgent: (data = {}) => request.post('/agent/update', data),
  deleteAgent: (params = {}) => request.delete('/agent/delete', { params }),
  getVoiceList: (params = {}) => request.get('/agent/voice/list', { params }),
  getLlmList: () => request.get('/agent/llm/list'),
  // resource-agentTemplate
  getAgentTemplateList: (params = {}) => request.get('/agent/template/list', { params }),
  createAgentTemplate: (data = {}) => request.post('/agent/template/create', data),
  updateAgentTemplate: (data = {}) => request.post('/agent/template/update', data),
  deleteAgentTemplate: (params = {}) => request.delete('/agent/template/delete', { params }),
  // resource-device
  getDeviceList: (params = {}) => request.get('/device/list', { params }),
  createDevice: (data = {}) => request.post('/device/create', data),
  updateDevice: (data = {}) => request.post('/device/update', data),
  deleteDevice: (params = {}) => request.delete('/device/delete', { params }),
  // resource-ota
  getOtaList: (params = {}) => request.get('/resource/ota/list', { params }),
  createOta: (data = {}) => request.post('/resource/ota/create', data),
  updateOta: (data = {}) => request.post('/resource/ota/update', data),
  deleteOta: (params = {}) => request.delete('/resource/ota/delete', { params }),
  uploadOtaFile: (data = {}) => request.post('/resource/ota/file', data, { timeout: 120000 }),
  // user-order
  getOrderList: (params = {}) => request.get('/order/list', { params }),
  createOrder: (data = {}) => request.post('/order/create', data),
  updateOrder: (data = {}) => request.post('/order/update', data),
  deleteOrder: (params = {}) => request.delete('/order/delete', { params }),
  // user-recharge
  getRechargeList: (params = {}) => request.get('/finance/recharge/list', { params }),
}
