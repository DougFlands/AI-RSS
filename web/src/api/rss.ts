import axios from 'axios'

/**
 * RSS API 接口封装
 */

// 获取所有 RSS 数据
export const getAllRss = async (params?: { date?: string }) => {
  const response = await axios.get('/api/rss/all', { params })
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