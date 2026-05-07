import axios from 'axios'

export const http = axios.create({ baseURL: '/api' })

export const Inbox = {
  listSources: () => http.get('/inbox/sources').then(r => r.data),
  createSource: (data) => http.post('/inbox/sources', data).then(r => r.data),
  fetchSource: (id) => http.post(`/inbox/sources/${id}/fetch`).then(r => r.data),
  deleteSource: (id) => http.delete(`/inbox/sources/${id}`).then(r => r.data),
  sourceTypes: () => http.get('/inbox/source-types').then(r => r.data),

  listItems: (params) => http.get('/inbox/items', { params }).then(r => r.data),
  rewrite: (id, ruleId) => http.post(`/inbox/items/${id}/rewrite`, null, { params: { rule_id: ruleId } }).then(r => r.data),
  setStatus: (id, status) => http.patch(`/inbox/items/${id}/status`, null, { params: { status } }).then(r => r.data),

  listRules: () => http.get('/inbox/rules').then(r => r.data),
  createRule: (data) => http.post('/inbox/rules', data).then(r => r.data),
  deleteRule: (id) => http.delete(`/inbox/rules/${id}`).then(r => r.data),
  runRules: () => http.post('/inbox/rules/run').then(r => r.data),
}

export const Posts = {
  list: () => http.get('/posts').then(r => r.data),
  get: (id) => http.get(`/posts/${id}`).then(r => r.data),
  create: (data) => http.post('/posts', data).then(r => r.data),
  update: (id, data) => http.patch(`/posts/${id}`, data).then(r => r.data),
  remove: (id) => http.delete(`/posts/${id}`).then(r => r.data),
  publish: (id, data) => http.post(`/posts/${id}/publish`, data).then(r => r.data),
}

export const Accounts = {
  list: () => http.get('/accounts').then(r => r.data),
  create: (data) => http.post('/accounts', data).then(r => r.data),
  remove: (id) => http.delete(`/accounts/${id}`).then(r => r.data),
  platforms: () => http.get('/accounts/platforms').then(r => r.data),
}

export const AI = {
  providers: () => http.get('/ai/providers').then(r => r.data),
  listConfigs: () => http.get('/ai/configs').then(r => r.data),
  createConfig: (data) => http.post('/ai/configs', data).then(r => r.data),
  activate: (id) => http.post(`/ai/configs/${id}/activate`).then(r => r.data),
  deleteConfig: (id) => http.delete(`/ai/configs/${id}`).then(r => r.data),
  chat: (data) => http.post('/ai/chat', data).then(r => r.data),
}
