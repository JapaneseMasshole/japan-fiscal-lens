<script setup>
import { computed, onMounted, ref } from 'vue'
import StatTile from '../components/StatTile.vue'
import { loadDataset } from '../data.js'
import { fy, yen } from '../format.js'
import { locale, t } from '../i18n.js'

const bs = ref(null)
const cost = ref(null)
onMounted(async () => {
  ;[bs.value, cost.value] = await Promise.all([
    loadDataset('national-balance-sheet'),
    loadDataset('national-operating-cost'),
  ])
})

const tiles = computed(() => {
  if (!bs.value || !cost.value) return []
  const last = (a) => a.at(-1)
  const trend = t('home.trend', { from: fy(bs.value.years[0]), to: fy(bs.value.years.at(-1)) })
  return [
    { label: t('home.assets'), value: yen(last(bs.value.totals.assets)), series: bs.value.totals.assets, color: 'var(--viz-series-1)', trend },
    { label: t('home.liabilities'), value: yen(last(bs.value.totals.liabilities)), series: bs.value.totals.liabilities, color: 'var(--viz-series-2)', trend },
    { label: t('home.cost'), value: yen(last(cost.value.totals.cost)), series: cost.value.totals.cost, color: 'var(--viz-series-2)', trend },
    {
      label: t('home.funding'),
      value: yen(last(cost.value.totals.funding)),
      note: t('home.fundingTax', { v: yen(last(cost.value.totals.funding_tax)) }),
      series: cost.value.totals.funding,
      color: 'var(--viz-series-1)',
      trend,
    },
  ]
})
const latest = computed(() => {
  if (!bs.value) return ''
  const y = bs.value.years.at(-1)
  const date = locale.value === 'ja' ? `${y + 1}年3月31日` : `31 March ${y + 1}`
  return t('home.latest', { year: fy(y), date })
})
</script>

<template>
  <section class="hero">
    <h1>{{ t('siteName') }}</h1>
    <p class="tagline">{{ t('tagline') }}</p>
  </section>

  <p v-if="latest" class="latest muted">{{ latest }}</p>
  <div class="tiles">
    <StatTile
      v-for="tile in tiles"
      :key="tile.label"
      :label="tile.label"
      :value="tile.value"
      :note="tile.note"
      :series="tile.series"
      :color="tile.color"
      :trend-label="tile.trend"
    />
  </div>
  <p v-if="tiles.length" class="disclaimer muted">{{ t('home.disclaimer') }}</p>

  <div class="grid">
    <RouterLink to="/national" class="tile-link">
      <h2>{{ t('national.title') }} →</h2>
      <p class="muted">{{ t('national.bs') }} · {{ t('national.costSection') }} · {{ t('national.cfSection') }}</p>
    </RouterLink>
    <RouterLink to="/local" class="tile-link">
      <h2>{{ t('local.title') }} →</h2>
      <p class="muted">{{ t('local.bs') }} · {{ t('local.cost') }} · {{ t('local.cf') }}</p>
    </RouterLink>
  </div>
</template>

<style scoped>
.hero { padding: 24px 0 8px; }
.hero h1 { font-size: 2rem; margin: 0; }
.tagline { font-size: 1.05rem; color: var(--muted); margin: 4px 0 0; }
.latest { margin: 16px 0 8px; font-size: 0.9rem; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); gap: 12px; }
.disclaimer { font-size: 0.8rem; margin: 8px 0 0; }
.tile-link { display: block; text-decoration: none; color: inherit; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }
.tile-link:hover { border-color: var(--accent); }
.tile-link p { margin: 0; font-size: 0.9rem; }
</style>
