<script setup>
import BalanceSheet from '../components/BalanceSheet.vue'
import ChartCard from '../components/ChartCard.vue'
import { t } from '../i18n.js'
</script>

<template>
  <h1>{{ t('national.title') }}</h1>

  <h2 class="section">{{ t('national.bs') }}</h2>
  <BalanceSheet />

  <div class="grid">
    <ChartCard :title="t('national.cost')" />
    <ChartCard :title="t('national.cf')" />
    <ChartCard :title="t('national.debt')" />
  </div>
</template>

<style scoped>
.section { margin: 1.5rem 0 0.75rem; font-size: 1.25rem; }
</style>
