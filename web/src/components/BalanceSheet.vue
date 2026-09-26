<script setup>
// National balance sheet: trend of totals, breakdown for a chosen year, full table.
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ChartCard from './ChartCard.vue'
import { loadDataset } from '../data.js'
import { cho, fy, pct, yen } from '../format.js'
import { locale, t } from '../i18n.js'
import { isDark, tokens } from '../theme.js'

const OTHER_THRESHOLD = 0.02 // items under 2% of a side's total are grouped as "Other"

const props = defineProps({ year: { type: Number, default: null } })
const data = ref(null)
const error = ref('')
const year = ref(null)
// The page-level year selector drives this; fall back to the latest year.
watch(
  () => [props.year, data.value],
  () => {
    const ys = data.value?.years ?? []
    year.value = ys.includes(props.year) ? props.year : (ys.at(-1) ?? null)
  },
)
const narrow = ref(window.innerWidth < 640)
const onResize = () => (narrow.value = window.innerWidth < 640)

onMounted(async () => {
  window.addEventListener('resize', onResize)
  try {
    data.value = await loadDataset('national-balance-sheet')
  } catch (e) {
    error.value = String(e)
  }
})
onBeforeUnmount(() => window.removeEventListener('resize', onResize))

const name = (line) => (locale.value === 'ja' ? line.item_ja : line.item_en || line.item_ja)
const unitLabel = computed(() => (locale.value === 'ja' ? '兆円' : '¥ trillion'))

function baseOption(tk) {
  return {
    textStyle: { fontFamily: tk.font, color: tk.text },
    animationDuration: 400,
    tooltip: {
      backgroundColor: tk.surface,
      borderColor: tk.grid,
      textStyle: { color: tk.text, fontFamily: tk.font },
      confine: true,
    },
  }
}

// ---- Chart 1: totals over time -------------------------------------------------
const trendOption = computed(() => {
  const d = data.value
  if (!d) return null
  const tk = tokens()
  void isDark.value
  const series = [
    ['assets', t('national.assets'), tk.series[0]],
    ['liabilities', t('national.liabilities'), tk.series[1]],
    ['net_assets', t('national.netAssets'), tk.series[2]],
  ]
  return {
    ...baseOption(tk),
    grid: { left: 8, right: narrow.value ? 16 : 96, top: narrow.value ? 72 : 48, bottom: 8, containLabel: true },
    legend: {
      top: 0,
      left: 0,
      itemWidth: 14,
      itemHeight: 2,
      icon: 'rect',
      itemStyle: { borderWidth: 0 }, // markers' surface ring must not hide the key
      textStyle: { color: tk.muted },
    },
    tooltip: {
      ...baseOption(tk).tooltip,
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: tk.axis, width: 1, type: 'solid' } },
      valueFormatter: (v) => yen(v * 10000),
    },
    xAxis: {
      type: 'category',
      data: d.years.map(fy),
      boundaryGap: false,
      axisLine: { onZero: false, lineStyle: { color: tk.grid } },
      axisTick: { show: false },
      axisLabel: { color: tk.axis },
    },
    yAxis: {
      type: 'value',
      name: unitLabel.value,
      nameTextStyle: { color: tk.axis, align: 'left' },
      axisLabel: { color: tk.axis, formatter: (v) => v.toLocaleString() },
      splitLine: { lineStyle: { color: tk.grid, width: 1 } },
    },
    series: series.map(([key, label, color], i) => ({
      name: label,
      type: 'line',
      color,
      data: d.totals[key].map(cho),
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { width: 2, color, cap: 'round', join: 'round' },
      itemStyle: { color, borderColor: tk.surface, borderWidth: 2 },
      emphasis: { focus: 'series' },
      endLabel: {
        show: !narrow.value,
        color: tk.text,
        formatter: (p) => yen(p.value * 10000, 0),
      },
      // Zero reference line, drawn once.
      ...(i === 2 && {
        markLine: {
          silent: true,
          symbol: 'none',
          label: { show: false },
          lineStyle: { color: tk.axis, width: 1, type: 'solid' },
          data: [{ yAxis: 0 }],
        },
      }),
    })),
  }
})

const trendAria = computed(() => {
  const d = data.value
  if (!d) return ''
  const last = d.years.length - 1
  return `${t('national.bsTrendTitle')}: ${fy(d.years[last])} ${t('national.assets')} ${yen(d.totals.assets[last])}, ${t('national.liabilities')} ${yen(d.totals.liabilities[last])}, ${t('national.netAssets')} ${yen(d.totals.net_assets[last])}`
})

// ---- Chart 2: breakdown for the selected year ---------------------------------
function breakdown(section) {
  const d = data.value
  const i = d.years.indexOf(year.value)
  const top = d.lines.filter((l) => l.section === section && l.parent_ja === '')
  const total = top.reduce((s, l) => s + l.values[i], 0)
  const big = []
  const small = []
  for (const l of top) (Math.abs(l.values[i]) / total >= OTHER_THRESHOLD ? big : small).push(l)
  const rows = big
    .map((l) => ({ label: name(l), value: l.values[i] }))
    .sort((a, b) => b.value - a.value)
  if (small.length) {
    rows.push({
      label: t('national.other', { n: small.length }),
      value: small.reduce((s, l) => s + l.values[i], 0),
      members: small.map(name),
    })
  }
  return { rows, total }
}

// Both breakdown charts share one scale, so bar lengths are comparable across them.
const sharedMax = computed(() => {
  if (!data.value || year.value == null) return null
  const m = Math.max(...['assets', 'liabilities'].flatMap((s) => breakdown(s).rows.map((r) => cho(r.value))))
  const step = 10 ** Math.floor(Math.log10(m)) / 5
  return Math.ceil(m / step) * step
})

function barOption(section, color) {
  const d = data.value
  if (!d || year.value == null) return null
  const tk = tokens()
  void isDark.value
  const { rows, total } = breakdown(section)
  return {
    ...baseOption(tk),
    grid: { left: 8, right: 72, top: 8, bottom: 8, containLabel: true },
    tooltip: {
      ...baseOption(tk).tooltip,
      trigger: 'item',
      formatter: (p) => {
        const r = rows[p.dataIndex]
        const wrap = document.createElement('div')
        const v = document.createElement('strong')
        v.textContent = yen(r.value)
        const n = document.createElement('div')
        n.textContent = `${r.label} · ${t('national.share')} ${pct(r.value / total)}`
        wrap.append(v, n)
        if (r.members) {
          const m = document.createElement('div')
          m.style.cssText = 'max-width:260px;white-space:normal;font-size:12px;opacity:.8'
          m.textContent = r.members.join('、')
          wrap.append(m)
        }
        return wrap
      },
    },
    xAxis: {
      type: 'value',
      min: 0,
      max: sharedMax.value,
      axisLabel: { color: tk.axis, formatter: (v) => v.toLocaleString(), hideOverlap: true },
      splitLine: { lineStyle: { color: tk.grid } },
      name: unitLabel.value,
      nameLocation: 'end',
      nameTextStyle: { color: tk.axis },
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: rows.map((r) => r.label),
      axisLine: { lineStyle: { color: tk.grid } },
      axisTick: { show: false },
      axisLabel: { color: tk.text, width: narrow.value ? 110 : 200, overflow: 'break' },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((r) => cho(r.value)),
        barMaxWidth: 18,
        itemStyle: { color, borderRadius: [0, 4, 4, 0] },
        emphasis: { itemStyle: { opacity: 0.85 } },
        label: {
          show: true,
          position: 'right',
          color: tk.text,
          formatter: (p) => yen(p.value * 10000),
        },
      },
    ],
  }
}

const assetsOption = computed(() => barOption('assets', tokens().series[0]))
const liabilitiesOption = computed(() => barOption('liabilities', tokens().series[1]))
const barHeight = (section) =>
  data.value && year.value != null ? breakdown(section).rows.length * 36 + 40 : 200

// ---- Table ---------------------------------------------------------------------
const tableRows = computed(() => {
  const d = data.value
  if (!d) return []
  const total = (key, label) => ({ label, values: d.totals[key], total: true, level: 0 })
  const bySection = (s) => d.lines.filter((l) => l.section === s).map((l) => ({ label: name(l), values: l.values, level: l.level }))
  return [
    ...bySection('assets'),
    total('assets', t('national.assets')),
    ...bySection('liabilities'),
    total('liabilities', t('national.liabilities')),
    total('net_assets', t('national.netAssets')),
  ]
})
const fmtCell = (v) =>
  Number.isFinite(v)
    ? cho(v).toLocaleString(locale.value === 'ja' ? 'ja-JP' : 'en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
    : '—'

const missingNotes = computed(() =>
  (data.value?.missing_years ?? []).map((m) =>
    t('national.missing', { year: fy(m.fiscal_year), reason: locale.value === 'ja' ? m.reason_ja : m.reason_en }),
  ),
)
const note = computed(() => data.value?.notes?.[0]?.[locale.value] ?? '')
</script>

<template>
  <p v-if="error" class="muted">{{ error }}</p>

  <ChartCard
    :title="t('national.bsTrendTitle')"
    :subtitle="t('national.bsTrendSub')"
    :option="trendOption"
    :source="data?.source"
    :aria-label="trendAria"
    :height="340"
  >
    <p v-for="m in missingNotes" :key="m" class="notice">{{ m }}</p>
    <p v-if="note" class="note">{{ note }}</p>
  </ChartCard>

  <template v-if="data">
    <div class="grid two">
      <ChartCard
        :title="`${t('national.assetsComp')}（${fy(year)}）`"
        :subtitle="t('national.compSub')"
        :option="assetsOption"
        :height="barHeight('assets')"
      />
      <ChartCard
        :title="`${t('national.liabilitiesComp')}（${fy(year)}）`"
        :subtitle="t('national.compSub')"
        :option="liabilitiesOption"
        :height="barHeight('liabilities')"
      />
    </div>

    <details class="card table-card">
      <summary>{{ t('national.table') }}（{{ unitLabel }}）</summary>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">{{ t('national.item') }}</th>
              <th v-for="y in data.years" :key="y" scope="col">{{ fy(y) }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in tableRows" :key="i" :class="{ total: r.total }">
              <th scope="row" :style="{ paddingLeft: `${8 + r.level * 16}px` }">{{ r.label }}</th>
              <td v-for="(v, j) in r.values" :key="j">{{ fmtCell(v) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </details>
  </template>
</template>

<style scoped>
.notice { font-size: 0.85rem; margin: 8px 0 0; padding: 8px 12px; border-radius: 6px; background: var(--bg); border: 1px solid var(--border); }
.note { font-size: 0.85rem; margin: 8px 0 0; color: var(--muted); }
.grid.two { margin: 12px 0 16px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.table-card { margin-bottom: 3rem; }
.table-card summary { cursor: pointer; font-weight: 600; }
.table-wrap { overflow-x: auto; margin-top: 12px; }
table { border-collapse: collapse; font-size: 0.85rem; min-width: 100%; }
th, td { padding: 4px 8px; border-bottom: 1px solid var(--border); white-space: nowrap; }
td { text-align: right; font-variant-numeric: tabular-nums; }
thead th { text-align: right; color: var(--muted); font-weight: 500; }
thead th:first-child, tbody th { text-align: left; font-weight: 400; }
thead th:first-child, tbody th { position: sticky; left: 0; background: var(--surface); }
tr.total th, tr.total td { font-weight: 700; }
</style>
