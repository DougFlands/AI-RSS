import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import './assets/styles/markdown.css'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import { registerServiceWorker } from './registerServiceWorker'

// 注册Service Worker
registerServiceWorker()

// 创建 queryClient 实例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5分钟
    },
  },
})

const app = createApp(App)
app.use(ElementPlus)
app.use(router)
// 使用解构的方式，提供 queryClient 实例
app.use(VueQueryPlugin, { queryClient })
app.mount('#app') 