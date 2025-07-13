import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  mode: 'hash',
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/recent-transactions',
      name: 'recent-transactions',
      component: () => import('@/views/RecentTransactionsView.vue')
    }
  ]
})

export default router
