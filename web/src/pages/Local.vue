<script setup>
import ComingNext from '../components/ComingNext.vue'
import { t, tm } from '../i18n.js'
</script>

<template>
  <h1>{{ t('local.title') }}</h1>
  <p class="muted">{{ t('local.intro') }}</p>
  <ComingNext :title="t('local.comingTitle')" :items="tm('local.coming')" />
</template>
