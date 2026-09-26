<script setup>
import ChartCard from '../components/ChartCard.vue'
import { t } from '../i18n.js'
</script>

<template>
  <h1>{{ t('local.title') }}</h1>
  <p class="muted">{{ t('local.intro') }}</p>
  <div class="grid">
    <ChartCard :title="t('local.bs')" />
    <ChartCard :title="t('local.cost')" />
    <ChartCard :title="t('local.cf')" />
  </div>
</template>
