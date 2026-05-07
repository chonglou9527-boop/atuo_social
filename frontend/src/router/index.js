import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/inbox' },
  { path: '/inbox', component: () => import('../views/Inbox.vue') },
  { path: '/sources', component: () => import('../views/Sources.vue') },
  { path: '/rules', component: () => import('../views/Rules.vue') },
  { path: '/posts', component: () => import('../views/Posts.vue') },
  { path: '/accounts', component: () => import('../views/Accounts.vue') },
  { path: '/ai', component: () => import('../views/AISettings.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
