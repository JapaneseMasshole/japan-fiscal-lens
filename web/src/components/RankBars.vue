<script setup>
// Ranked horizontal bars: one highlighted item, the rest in context gray, with an
// average reference line. Items with "not calculated" values are listed in text,
// never drawn as zero.
import { computed } from 'vue'
import ChartCard from './ChartCard.vue'
import { base } from '../charts.js'
import { t } from '../i18n.js'
import { NC, fmtInd, isNum, label } from '../local.js'
import { isDark, tokens } from '../theme.js'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  meta: { type: Object, required: true },
  rows: { type: Array, required: true }, // { name, value, highlight }
  average: { type: [Number, String, null], default: null },
  averageLabel: { type: String, default: '' },
  narrow: Boolean,
})

const ranked = computed(() => props.rows.filter((r) => isNum(r.value)).sort((a, b) => b.value - a.value))
const notCalculated = computed(() => props.rows.filter((r) => r.value === NC))
const fullSubtitle = computed(() =>
  isNum(props.average)
    ? `${props.subtitle} ${t('local.avgLine', { label: props.averageLabel, v: fmtInd(props.average, props.meta) })}`
    : props.subtitle,
)
const highlightRank = computed(() => ranked.value.findIndex((r) => r.highlight) + 1)

const ROW = 18
const height = computed(() => Math.max(160, ranked.value.length * ROW + 56))

const option = computed(() => {
  void isDark.value
  const tk = tokens()
  const rows = ranked.value
  return {
    ...base(tk),
    animation: false,
    grid: { left: 8, right: 64, top: 24, bottom: 8, containLabel: true },
    tooltip: {
      ...base(tk).tooltip,
      trigger: 'item',
      formatter: (p) => {
        const r = rows[p.dataIndex]
        const wrap = document.createElement('div')
        const v = document.createElement('strong')
        v.textContent = fmtInd(r.value, props.meta)
        wrap.append(v, document.createTextNode(`  ${r.name}（${p.dataIndex + 1}/${rows.length}）`))
        return wrap
      },
    },
    xAxis: {
      type: 'value',
      position: 'top',
      axisLabel: { color: tk.axis, hideOverlap: true },
      splitLine: { lineStyle: { color: tk.grid } },
      min: (v) => Math.min(0, v.min),
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: rows.map((r) => r.name),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: tk.grid } },
      axisLabel: {
        interval: 0,
        fontSize: 11,
        color: tk.muted,
        formatter: (n, i) => (rows[i]?.highlight ? `{hl|${n}}` : n),
        rich: { hl: { color: tk.text, fontWeight: 700, fontSize: 12 } },
      },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 12,
        data: rows.map((r) => ({
          value: r.value,
          itemStyle: {
            color: r.highlight ? tk.series[0] : tk.context,
            borderRadius: r.value < 0 ? [4, 0, 0, 4] : [0, 4, 4, 0],
          },
          label: r.highlight
            ? { show: true, position: r.value < 0 ? 'left' : 'right', color: tk.text, fontWeight: 700, formatter: () => fmtInd(r.value, props.meta) }
            : { show: false },
        })),
        markLine: isNum(props.average)
          ? {
              silent: true,
              symbol: 'none',
              lineStyle: { color: tk.reference, width: 1, type: 'solid' },
              label: { show: false }, // stated in the subtitle instead (a line label clips at the edge)
              data: [{ xAxis: props.average }],
            }
          : undefined,
      },
    ],
  }
})
</script>

<template>
  <ChartCard :title="title" :subtitle="fullSubtitle" :option="ranked.length ? option : null" :height="height">
    <p v-if="highlightRank" class="rank">
      {{ t('local.rank', { rank: highlightRank, n: ranked.length, indicator: label(meta) }) }}
    </p>
    <p v-if="notCalculated.length" class="nc">
      <strong>{{ t('local.nc') }}（{{ notCalculated.length }}）</strong>:
      <span v-for="(r, i) in notCalculated" :key="r.name" :class="{ hl: r.highlight }">{{ r.name }}{{ i < notCalculated.length - 1 ? '、' : '' }}</span>
    </p>
  </ChartCard>
</template>

<style scoped>
.rank { font-size: 0.85rem; margin: 8px 0 0; }
.nc { font-size: 0.8rem; color: var(--muted); margin: 6px 0 0; line-height: 1.6; }
.nc .hl { color: var(--text); font-weight: 700; }
</style>
