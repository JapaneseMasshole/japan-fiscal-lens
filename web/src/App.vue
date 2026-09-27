<script setup>
import { locale, t } from './i18n.js'

function toggleLocale() {
  locale.value = locale.value === 'ja' ? 'en' : 'ja'
  document.documentElement.lang = locale.value
}
</script>

<template>
  <header class="site-header">
    <div class="container bar">
      <RouterLink to="/" class="brand">{{ t('siteName') }}</RouterLink>
      <nav>
        <RouterLink to="/national">{{ t('nav.national') }}</RouterLink>
        <RouterLink to="/statements">{{ t('nav.statements') }}</RouterLink>
        <RouterLink to="/local">{{ t('nav.local') }}</RouterLink>
        <RouterLink to="/methodology">{{ t('nav.methodology') }}</RouterLink>
        <button class="lang" @click="toggleLocale">{{ locale === 'ja' ? 'EN' : '日本語' }}</button>
      </nav>
    </div>
  </header>
  <main class="container">
    <RouterView />
  </main>
  <footer class="container muted footer">
    <a href="https://github.com/JapaneseMasshole/japan-fiscal-lens">GitHub</a>
  </footer>
</template>

<style scoped>
.site-header { border-bottom: 1px solid var(--border); background: var(--surface); }
.bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 56px; flex-wrap: wrap; }
.brand { font-weight: 700; text-decoration: none; color: var(--text); }
nav { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
nav a { text-decoration: none; color: var(--muted); }
nav a.router-link-active { color: var(--text); font-weight: 600; }
.lang { border: 1px solid var(--border); background: transparent; color: var(--text); border-radius: 6px; padding: 2px 10px; cursor: pointer; font: inherit; }
.footer { padding: 24px 16px; font-size: 0.85rem; }
</style>
