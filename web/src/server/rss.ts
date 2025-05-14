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
  sources: 'rss-sources',
  new: 'rss-new',
}

// 获取所有 RSS
export interface RssQueryParams {
  date?: string
  preference?: 'liked' | 'disliked' | 'unmarked' | 'recommended' | 'all'
  source_id?: string
}

// 获取所有 RSS
export const useRssQuery = (params: RssQueryParams) => {
  return useQuery({
    queryKey: [params.date, params.preference, params.source_id],
    queryFn: () => api.rss.getAllRss(params),
    // 禁用不必要的选项
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  })
}

// 获取最新 RSS 数据
export const useNewRssQuery = () => {
  const queryClient = useQueryClient()
  
  const query = useQuery({
    queryKey: [RSS_QUERIES.new],
    queryFn: () => api.rss.getNewRss(),
    // 禁用自动刷新
    enabled: false,
  })
  
  // 重写 refetch 方法，在成功后使相关查询失效
  const refetchAndInvalidate = async () => {
    const result = await query.refetch()
    
    // 请求成功后，使相关查询失效
    if (result.isSuccess) {
      // 刷新所有 RSS 相关数据
      queryClient.invalidateQueries({ queryKey: [RSS_QUERIES.all] })
      queryClient.invalidateQueries({ queryKey: [RSS_QUERIES.dates] })
      queryClient.invalidateQueries({ queryKey: [RSS_QUERIES.sources] })
    }
    
    return result
  }
  
  return {
    ...query,
    refetch: refetchAndInvalidate
  }
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

// 获取RSS订阅源列表
export const useRssSourcesQuery = () => {
  return useQuery({
    queryKey: [RSS_QUERIES.sources],
    queryFn: () => api.rss.getRssSources(),
    // 禁用不必要的选项
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  })
} 