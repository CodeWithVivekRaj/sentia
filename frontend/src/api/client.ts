import axios from 'axios'

const BASE = '/api'

export const api = axios.create({
  baseURL: BASE,
  timeout: 30000,
})

export const health = () => axios.get('/health').then(r => r.data)

export const getState = () => api.get('/state').then(r => r.data)

export const getEvents = (limit = 50, since = 0) =>
  api.get('/state/events', { params: { limit, since } }).then(r => r.data)

export const toggleLLM = (enabled: boolean) =>
  api.post('/state/llm/toggle', null, { params: { enabled } }).then(r => r.data)

export const listModels = () => api.get('/models').then(r => r.data)

export const selectModel = (model: string) =>
  api.post('/models/select', { model }).then(r => r.data)

export const sendChat = (content: string) =>
  api.post('/chat', { content }).then(r => r.data)

export const getNotifyStatus = () => api.get('/notify/status').then(r => r.data)
export const sendTestNotification = () => api.post('/notify/test').then(r => r.data)
