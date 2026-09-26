import { createRouter, createWebHashHistory } from 'vue-router'

// Hash history works on GitHub Pages without server-side rewrites.
export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: () => import('./pages/Overview.vue') },
    { path: '/national', component: () => import('./pages/National.vue') },
    { path: '/local', component: () => import('./pages/Local.vue') },
    { path: '/methodology', component: () => import('./pages/Methodology.vue') },
  ],
  scrollBehavior: () => ({ top: 0 }),
})
