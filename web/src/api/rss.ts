import axios from 'axios'

/**
 * RSS API 接口封装
 */

// 获取所有 RSS 数据
export const getNewRss = async () => {
  const response = await axios.get('/api/rss')
  return response.data
}


// 获取所有 RSS 数据
export const getAllRss = async (params?: { date?: string }) => {
  // 设置大限制值以获取所有数据
  const requestParams = { 
    ...params,
    limit: 1000 // 设置大值以获取全部数据
  }
  const response = await axios.get('/api/rss/all', { params: requestParams })
  return response.data
}

// 获取日期列表
export const getRssDates = async () => {
  const response = await axios.get('/api/rss/dates')
  return response.data
}

// 根据关键字搜索 RSS
export const searchRss = async (query: string, n_results = 30) => {
  const response = await axios.post('/api/rss/story', { query, n_results })
  return response.data
}

// 更新 RSS 偏好设置
export interface PreferenceParams {
  feed_id: string
  is_liked: boolean
  reason?: string
}

export const updateRssPreference = async (params: PreferenceParams) => {
  const response = await axios.post('/api/rss/preference', params)
  return response.data
}

// 获取RSS源列表
export const getRssSources = async () => {
  const response = await axios.get('/api/rss/sources')
  return response.data
}

// 添加RSS源
export interface AddSourceParams {
  url: string
  name?: string
}

export const addRssSource = async (params: AddSourceParams) => {
  const response = await axios.post('/api/rss/sources', params)
  return response.data
}

// 更新RSS源
export const updateRssSource = async (sourceId: string, params: AddSourceParams) => {
  const response = await axios.put(`/api/rss/sources/${sourceId}`, params)
  return response.data
}

// 删除RSS源
export const deleteRssSource = async (sourceId: string) => {
  const response = await axios.delete(`/api/rss/sources/${sourceId}`)
  return response.data
} 