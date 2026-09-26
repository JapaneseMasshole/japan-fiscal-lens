<script setup>
// One indicator over time: the selected government vs. the official average.
// Legal thresholds are drawn only when the data comes within reach of them;
// otherwise they are stated in text, so a distant line does not flatten the trend.
import { computed } from 'vue'
import ChartCard from './ChartCard.vue'
import { base, legend } from '../charts.js'
import { fy } from '../format.js'
import { t } from '../i18n.js'
import { NC, desc, fmtInd, isNum, label, thresholdLabel, thresholdsFor } from '../local.js'
import { isDark, tokens } from '../theme.js'

const props = defineProps({
  meta: { type: Object, required: true },
  years: { type: Array, required: true },
  name: { type: String, required: true },
  values: { type: Array, required: true },
  average: { type: Array, required: true },
  averageLabel: { type: String, required: true },
  isPrefecture: Boolean,
  isDesignated: Boolean,
  narrow: Boolean,
})

const thresholds = computed(() => thresholdsFor(props.meta, props))
const dataMax = computed(() => Math.max(0, ...[...props.values, ...props.average].filter(isNum)))
const drawn = computed(() => thresholds.value.filter((th) => dataMax.value >= th.value * 0.5))
const stated = computed(() => thresholds.value.filter((th) => !drawn.value.includes(th)))
function niceCeil(x) {
  const step = 10 ** Math.floor(Math.log10(x)) / 2
  return Math.ceil(x / step) * step
}
const ncYears = computed(() => props.years.filter((y, i) => props.values[i] === NC))

const option = computed(() => {
  void isDark.value
  const tk = tokens()
  const num = (arr) => arr.map((v) => (isNum(v) ? v : null))
  const line = (name, data, color, extra = {}) => ({
    name,
    type: 'line',
    data,
    color,
    symbol: 'circle',
    symbolSize: 8,
    connectNulls: false,
    lineStyle: { width: 2, color },
    itemStyle: { color, borderColor: tk.surface, borderWidth: 2 },
    endLabel: { show: !props.narrow, color: tk.text, formatter: (p) => fmtInd(p.value, props.meta) },
    ...extra,
  })
  return {
    ...base(tk),
    grid: { left: 8, right: props.narrow ? 16 : 64, top: 44, bottom: 8, containLabel: true },
    legend: legend(tk, 'roundRect'),
    tooltip: {
      ...base(tk).tooltip,
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: tk.axis, width: 1, type: 'solid' } },
      formatter: (ps) => {
        const i = ps[0].dataIndex
        const wrap = document.createElement('div')
        const h = document.createElement('div')
        h.textContent = fy(props.years[i])
        wrap.append(h)
        for (const [n, arr] of [[props.name, props.values], [props.averageLabel, props.average]]) {
          const row = document.createElement('div')
          const b = document.createElement('strong')
          b.textContent = fmtInd(arr[i], props.meta)
          row.append(b, document.createTextNode(`  ${n}`))
          wrap.append(row)
        }
        return wrap
      },
    },
    xAxis: {
      type: 'category',
      data: props.years.map(fy),
      boundaryGap: false,
      axisLine: { onZero: false, lineStyle: { color: tk.grid } },
      axisTick: { show: false },
      axisLabel: { color: tk.axis, hideOverlap: true },
    },
    yAxis: {
      type: 'value',
      scale: props.meta.key === 'laspeyres',
      name: props.meta.unit,
      nameTextStyle: { color: tk.axis, align: 'left' },
      axisLabel: { color: tk.axis },
      splitLine: { lineStyle: { color: tk.grid, width: 1 } },
      // Make room for drawn thresholds, rounded to a clean tick.
      max: drawn.value.length ? (v) => niceCeil(Math.max(v.max, ...drawn.value.map((th) => th.value)) * 1.05) : null,
    },
    series: [
      line(props.name, num(props.values), tk.series[0], {
        markLine: drawn.value.length
          ? {
              silent: true,
              symbol: 'none',
              lineStyle: { color: tk.reference, width: 1, type: 'solid' },
              label: { color: tk.muted, position: 'insideEndTop', formatter: (p) => p.name },
              data: drawn.value.map((th) => ({ yAxis: th.value, name: thresholdLabel(th) })),
            }
          : undefined,
      }),
      line(props.averageLabel, num(props.average), tk.reference, {
        symbolSize: 6,
        endLabel: { show: false },
      }),
    ],
  }
})
</script>

<template>
  <ChartCard :title="label(meta)" :subtitle="desc(meta)" :option="option" :height="260">
    <p v-if="stated.length" class="note">
      {{ t('local.thresholdText') }} {{ stated.map(thresholdLabel).join(' / ') }}
    </p>
    <p v-if="ncYears.length" class="note">
      {{ t('local.ncYears', { years: ncYears.map(fy).join('、') }) }}
    </p>
  </ChartCard>
</template>

<style scoped>
.note { font-size: 0.8rem; color: var(--muted); margin: 6px 0 0; }
</style>
