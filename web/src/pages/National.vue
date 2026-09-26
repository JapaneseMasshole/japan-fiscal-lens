<script setup>
import ChartCard from '../components/ChartCard.vue'
import { t } from '../i18n.js'
</script>

<template>
  <h1>{{ t('national.title') }}</h1>
  <div class="grid">
    <ChartCard :title="t('national.bs')" />
    <ChartCard :title="t('national.cost')" />
    <ChartCard :title="t('national.cf')" />
    <ChartCard :title="t('national.debt')" />
  </div>
</template>
