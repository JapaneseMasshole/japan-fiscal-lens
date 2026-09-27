<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import BalanceSheet from '../components/BalanceSheet.vue'
import CashFlow from '../components/CashFlow.vue'
import OperatingCost from '../components/OperatingCost.vue'
import { loadIndex } from '../data.js'
import { fy } from '../format.js'
import { t } from '../i18n.js'

const years = ref([])
const year = ref(null)
const narrow = ref(window.innerWidth < 640)
const onResize = () => (narrow.value = window.innerWidth < 640)

onMounted(async () => {
  window.addEventListener('resize', onResize)
  const index = await loadIndex()
  const ds = index.datasets.find((d) => d.id === 'national-balance-sheet')
  if (ds) {
    for (let y = ds.years[1]; y >= ds.years[0]; y--) years.value.push(y)
    year.value = years.value[0]
  }
})
onBeforeUnmount(() => window.removeEventListener('resize', onResize))
</script>

<template>
  <h1>{{ t('statements.title') }}</h1>
  <p class="muted intro">{{ t('statements.intro') }}</p>

  <!-- One filter row above all charts: the year used by every breakdown. -->
  <div v-if="years.length" class="controls">
    <label>
      {{ t('national.yearPicker') }}
      <select v-model.number="year">
        <option v-for="y in years" :key="y" :value="y">{{ fy(y) }}</option>
      </select>
    </label>
  </div>

  <h2 id="bs" class="section">{{ t('national.bs') }}</h2>
  <BalanceSheet :year="year" />

  <h2 id="cost" class="section">{{ t('national.costSection') }}</h2>
  <OperatingCost :year="year" :narrow="narrow" />

  <h2 id="cf" class="section">{{ t('national.cfSection') }}</h2>
  <CashFlow :narrow="narrow" />

  <div class="end" />
</template>

<style scoped>
.section { margin: 2rem 0 0.75rem; font-size: 1.25rem; }
.intro { margin: 0; max-width: 46rem; }
.end { height: 48px; }
.controls {
  position: sticky; top: 0; z-index: 5;
  display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
  margin: 12px -16px 0; padding: 10px 16px;
  background: color-mix(in srgb, var(--bg) 92%, transparent);
  backdrop-filter: blur(6px);
  border-bottom: 1px solid var(--border);
}
.controls select { margin-left: 8px; font: inherit; padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border); background: var(--surface); color: var(--text); }
</style>
