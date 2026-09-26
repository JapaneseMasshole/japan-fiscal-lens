<script setup>
// Cash flow by category (区分別収支計算書): operating / financing / net per year, and bonds.
import { computed, onMounted, ref } from 'vue'
import ChartCard from './ChartCard.vue'
import DataTable from './DataTable.vue'
import { loadDataset } from '../data.js'
import { fy } from '../format.js'
import { locale, t } from '../i18n.js'
import { isDark, tokens } from '../theme.js'
import { axisTooltip, base, columns, legend, valueAxis, yearAxis, zeroLine } from '../charts.js'

const props = defineProps({ narrow: Boolean })
const data = ref(null)
onMounted(async () => (data.value = await loadDataset('national-cash-flow')))
const name = (l) => (locale.value === 'ja' ? l.item_ja : l.item_en || l.item_ja)

function frame(tk, d) {
  return {
    ...base(tk),
    grid: { left: 8, right: 16, top: props.narrow ? 72 : 48, bottom: 8, containLabel: true },
    legend: legend(tk),
    tooltip: axisTooltip(tk),
    xAxis: yearAxis(tk, d.years),
    yAxis: valueAxis(tk),
  }
}

const flowOption = computed(() => {
  const d = data.value
  if (!d) return null
  void isDark.value
  const tk = tokens()
  return {
    ...frame(tk, d),
    series: [
      columns(tk, t('national.cfOperating'), d.totals.operating, tk.series[0], { markLine: zeroLine(tk) }),
      columns(tk, t('national.cfFinancing'), d.totals.financing, tk.series[1]),
      columns(tk, t('national.cfNet'), d.totals.net, tk.series[2]),
    ],
  }
})

// Redemptions are negative in the statement; shown as positive amounts next to issuance.
const bondOption = computed(() => {
  const d = data.value
  if (!d) return null
  void isDark.value
  const tk = tokens()
  return {
    ...frame(tk, d),
    series: [
      columns(tk, t('national.bondIssue'), d.totals.bond_issuance, tk.series[0]),
      columns(tk, t('national.bondRedeem'), d.totals.bond_redemption.map((v) => (v == null ? null : -v)), tk.series[1]),
    ],
  }
})

const tableRows = computed(() => {
  const d = data.value
  if (!d) return []
  let last = ''
  return d.lines.map((l) => {
    const heading = l.heading && l.heading !== last ? l.heading : ''
    last = l.heading || last
    const isTotal = ['業務収支', '財務収支', '本年度収支', '本年度末現金･預金残高'].includes(l.item_ja)
    return { label: name(l), values: l.values, heading, total: isTotal, level: isTotal ? 0 : 1 }
  })
})
const note = computed(() => data.value?.notes?.[0]?.[locale.value] ?? '')
</script>

<template>
  <div class="grid two">
    <ChartCard
      :title="t('national.cfTitle')"
      :subtitle="t('national.cfSub')"
      :option="flowOption"
      :source="data?.source"
      :height="320"
    >
      <p v-if="note" class="note">{{ note }}</p>
    </ChartCard>
    <ChartCard
      :title="t('national.bondTitle')"
      :subtitle="t('national.bondSub')"
      :option="bondOption"
      :source="data?.source"
      :height="320"
    />
  </div>
  <DataTable v-if="data" :years="data.years" :rows="tableRows" />
</template>

<style scoped>
.note { font-size: 0.85rem; margin: 8px 0 0; color: var(--muted); }
.grid.two { margin: 0 0 16px; }
</style>
