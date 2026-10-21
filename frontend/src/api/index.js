import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 120000 })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.message || err.message || '请求失败'
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') window.location.href = '/login'
    }
    return Promise.reject(new Error(msg))
  },
)

export default http

// 模型提供商
export const getModels = () => http.get('/models')

// 认证
export const login = (username, password) => http.post('/auth/login', { username, password })
export const register = (username, password) => http.post('/auth/register', { username, password })

// 数据集
export const listDatasets = () => http.get('/datasets')
export const uploadDataset = (file) => {
  const fd = new FormData()
  fd.append('file', file)
  return http.post('/datasets/upload', fd)
}
export const renameDataset = (id, name) => http.patch(`/datasets/${id}`, { name })
export const deleteDataset = (id) => http.delete(`/datasets/${id}`)
export const getDatasetMeta = (id) => http.get(`/datasets/${id}/meta`)

// 报告
export const generateReport = (payload) => http.post('/reports/generate', payload)
export const getReportStatus = (taskId) => http.get(`/reports/${taskId}`)
