<script setup>
// Operating cost (業務費用) vs funding (財源) by year, plus the cost breakdown for one year.
import { computed, onMounted, ref } from 'vue'
import ChartCard from './ChartCard.vue'
import DataTable from './DataTable.vue'
import { loadDataset } from '../data.js'
import { fy } from '../format.js'
import { locale, t } from '../i18n.js'
import { isDark, tokens } from '../theme.js'
import { axisTooltip, base, columns, foldRows, hbars, hbarsHeight, legend, valueAxis, yearAxis } from '../charts.js'

const props = defineProps({ year: { type: Number, default: null }, narrow: Boolean })
const data = ref(null)
onMounted(async () => (data.value = await loadDataset('national-operating-cost')))

const name = (l) => (locale.value === 'ja' ? l.item_ja : l.item_en || l.item_ja)
const yearIndex = computed(() => {
  const d = data.value
  if (!d) return -1
  const i = d.years.indexOf(props.year)
  return i >= 0 ? i : d.years.length - 1
})

const trendOption = computed(() => {
  const d = data.value
  if (!d) return null
  void isDark.value
  const tk = tokens()
  return {
    ...base(tk),
    grid: { left: 8, right: 16, top: props.narrow ? 72 : 48, bottom: 8, containLabel: true },
    legend: legend(tk),
    tooltip: axisTooltip(tk),
    xAxis: yearAxis(tk, d.years),
    yAxis: valueAxis(tk),
    series: [
      columns(tk, t('national.costTotal'), d.totals.cost, tk.series[1]),
      columns(tk, t('national.fundingTax'), d.totals.funding_tax, tk.series[0], { stack: 'funding' }),
      columns(tk, t('national.fundingOther'), d.totals.funding_other, tk.series[2], { stack: 'funding' }),
    ].map((s, i) =>
      // Only the top of a stack gets the rounded end; the cost column keeps its own.
      i === 1 ? { ...s, data: s.data.map((x) => ({ ...x, itemStyle: { borderRadius: 0 } })) } : s,
    ),
  }
})

const breakdown = computed(() => {
  const d = data.value
  if (!d) return null
  return foldRows(d.lines, yearIndex.value, name)
})
const breakdownOption = computed(() => {
  if (!breakdown.value) return null
  void isDark.value
  const tk = tokens()
  const { rows, total } = breakdown.value
  return hbars(tk, rows, total, tk.series[1], { narrow: props.narrow })
})

const tableRows = computed(() => {
  const d = data.value
  if (!d) return []
  return [
    ...d.lines.map((l) => ({ label: name(l), values: l.values })),
    { label: t('national.costTotal'), values: d.totals.cost, total: true },
    { label: t('national.fundingTax'), values: d.totals.funding_tax },
    { label: t('national.fundingOther'), values: d.totals.funding_other },
    { label: t('national.fundingTotal'), values: d.totals.funding, total: true },
  ]
})
const note = computed(() => data.value?.notes?.[0]?.[locale.value] ?? '')
const missing = computed(() =>
  (data.value?.missing_years ?? []).map((m) =>
    t('national.missing', { year: fy(m.fiscal_year), reason: locale.value === 'ja' ? m.reason_ja : m.reason_en }),
  ),
)
</script>

<template>
  <ChartCard
    :title="t('national.costTrendTitle')"
    :subtitle="t('national.costTrendSub')"
    :option="trendOption"
    :source="data?.source"
    :height="340"
  >
    <p v-for="m in missing" :key="m" class="notice">{{ m }}</p>
    <p v-if="note" class="note">{{ note }}</p>
  </ChartCard>
  <div v-if="data" class="grid one">
    <ChartCard
      :title="`${t('national.costComp')}（${fy(data.years[yearIndex])}）`"
      :subtitle="t('national.compSubSingle')"
      :option="breakdownOption"
      :height="hbarsHeight(breakdown.rows.length)"
    />
  </div>
  <DataTable v-if="data" :years="data.years" :rows="tableRows" />
</template>

<style scoped>
.notice { font-size: 0.85rem; margin: 8px 0 0; padding: 8px 12px; border-radius: 6px; background: var(--bg); border: 1px solid var(--border); }
.note { font-size: 0.85rem; margin: 8px 0 0; color: var(--muted); }
.grid.one { grid-template-columns: 1fr; margin: 16px 0; }
</style>
