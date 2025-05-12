import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { api } from '../api'
import type { PreferenceParams } from '../api/rss'

/**
 * RSS Server 层，使用 TanStack Query 封装 API 调用
 */

// 查询键
export const RSS_QUERIES = {
  all: 'rss-all',
  dates: 'rss-dates',
  search: 'rss-search',
}

// 获取所有 RSS
export const useRssQuery = (date?: string) => {
  return useQuery({
    queryKey: [RSS_QUERIES.all, date],
    queryFn: () => api.rss.getAllRss({ date }),
    // 禁用不必要的选项
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  })
}

// 获取日期列表
export const useRssDatesQuery = () => {
  return useQuery({
    queryKey: [RSS_QUERIES.dates],
    queryFn: () => api.rss.getRssDates(),
    // 禁用不必要的选项
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  })
}

// 搜索 RSS
export const useRssSearchQuery = (query: string, enabled = false) => {
  return useQuery({
    queryKey: [RSS_QUERIES.search, query],
    queryFn: () => api.rss.searchRss(query),
    enabled: enabled && !!query,
    // 禁用不必要的选项
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  })
}

// 更新 RSS 偏好
export const useUpdateRssPreferenceMutation = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (params: PreferenceParams) => api.rss.updateRssPreference(params),
    onSuccess: () => {
      // 成功后刷新 RSS 数据
      queryClient.invalidateQueries({ queryKey: [RSS_QUERIES.all] })
    },
  })
} 