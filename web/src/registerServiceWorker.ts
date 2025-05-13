import { registerSW } from 'virtual:pwa-register'

export function registerServiceWorker() {
  const updateSW = registerSW({
    onNeedRefresh() {
      // 当有新版本时提示用户
      console.log('有新内容可用，请刷新')
    },
    onOfflineReady() {
      // 当应用可离线使用时
      console.log('应用已准备好离线使用')
    },
  })

  return updateSW
} 