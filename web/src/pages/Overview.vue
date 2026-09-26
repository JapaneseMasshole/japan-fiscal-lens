<script setup>
import { t } from '../i18n.js'
</script>

<template>
  <h1>{{ t('siteName') }}</h1>
  <p class="muted">{{ t('tagline') }}</p>
  <div class="grid">
    <RouterLink to="/national" class="tile">
      <h2>{{ t('national.title') }}</h2>
      <p class="muted">{{ t('national.bs') }} · {{ t('national.cost') }} · {{ t('national.cf') }}</p>
    </RouterLink>
    <RouterLink to="/local" class="tile">
      <h2>{{ t('local.title') }}</h2>
      <p class="muted">{{ t('local.bs') }} · {{ t('local.cost') }} · {{ t('local.cf') }}</p>
    </RouterLink>
  </div>
</template>

<style scoped>
.tile { display: block; text-decoration: none; color: inherit; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }
.tile:hover { border-color: var(--accent); }
.tile p { margin: 0; font-size: 0.9rem; }
</style>
