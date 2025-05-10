import { createRouter, createWebHistory } from 'vue-router'
// @ts-ignore
import RssView from '../views/RssView.vue'

const routes = [
  {
    path: '/',
    name: 'rss',
    component: RssView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 