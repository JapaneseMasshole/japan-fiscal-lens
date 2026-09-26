// Shared ECharts option builders, so every chart follows the same mark specs:
// 2px lines, >=8px markers with a surface ring, <=18px bars with 4px rounded data-ends,
// hairline solid grid, text in text tokens (never the series color).
import { cho, fy, pct, yen } from './format.js'
import { locale, t } from './i18n.js'

export const OTHER_THRESHOLD = 0.02

export const unitLabel = () => (locale.value === 'ja' ? '兆円' : '¥ trillion')

export function base(tk) {
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

export function legend(tk, icon = 'rect') {
  return {
    top: 0,
    left: 0,
    itemWidth: 14,
    itemHeight: icon === 'rect' ? 10 : 2,
    icon,
    itemStyle: { borderWidth: 0 },
    textStyle: { color: tk.muted },
  }
}

export function yearAxis(tk, years, boundaryGap = true) {
  return {
    type: 'category',
    data: years.map(fy),
    boundaryGap,
    axisLine: { onZero: false, lineStyle: { color: tk.grid } },
    axisTick: { show: false },
    axisLabel: { color: tk.axis },
  }
}

export function valueAxis(tk) {
  return {
    type: 'value',
    name: unitLabel(),
    nameTextStyle: { color: tk.axis, align: 'left' },
    axisLabel: { color: tk.axis, formatter: (v) => v.toLocaleString() },
    splitLine: { lineStyle: { color: tk.grid, width: 1 } },
  }
}

export const zeroLine = (tk) => ({
  silent: true,
  symbol: 'none',
  label: { show: false },
  lineStyle: { color: tk.axis, width: 1, type: 'solid' },
  data: [{ yAxis: 0 }],
})

// Column series (vertical). Rounded data-end away from the baseline, for negatives too.
export function columns(tk, name, values, color, extra = {}) {
  return {
    name,
    type: 'bar',
    data: values.map((v) => ({
      value: v == null ? null : cho(v),
      itemStyle: { borderRadius: v < 0 ? [0, 0, 4, 4] : [4, 4, 0, 0] },
    })),
    color,
    barMaxWidth: 18,
    barGap: '15%',
    itemStyle: { color, borderColor: tk.surface, borderWidth: 1 },
    emphasis: { itemStyle: { opacity: 0.85 } },
    ...extra,
  }
}

export function axisTooltip(tk) {
  return {
    ...base(tk).tooltip,
    trigger: 'axis',
    axisPointer: { type: 'shadow', shadowStyle: { color: tk.grid, opacity: 0.35 } },
    valueFormatter: (v) => (v == null ? '—' : yen(v * 10000)),
  }
}

// Top-level lines for one year → rows sorted by size, small ones folded into "Other".
export function foldRows(lines, i, nameOf) {
  const total = lines.reduce((s, l) => s + (l.values[i] ?? 0), 0)
  const big = []
  const small = []
  for (const l of lines) {
    const v = l.values[i]
    if (v == null) continue
    ;(Math.abs(v) / total >= OTHER_THRESHOLD ? big : small).push(l)
  }
  const rows = big.map((l) => ({ label: nameOf(l), value: l.values[i] })).sort((a, b) => b.value - a.value)
  if (small.length) {
    rows.push({
      label: t('national.other', { n: small.length }),
      value: small.reduce((s, l) => s + l.values[i], 0),
      members: small.map(nameOf),
    })
  }
  return { rows, total }
}

// Horizontal single-series bar chart with values at the bar tips.
export function hbars(tk, rows, total, color, { max = null, narrow = false } = {}) {
  return {
    ...base(tk),
    grid: { left: 8, right: 80, top: 8, bottom: 8, containLabel: true },
    tooltip: {
      ...base(tk).tooltip,
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
          m.textContent = r.members.join(locale.value === 'ja' ? '、' : ', ')
          wrap.append(m)
        }
        return wrap
      },
    },
    xAxis: {
      type: 'value',
      min: 0,
      max,
      axisLabel: { color: tk.axis, formatter: (v) => v.toLocaleString(), hideOverlap: true },
      splitLine: { lineStyle: { color: tk.grid } },
      name: unitLabel(),
      nameLocation: 'end',
      nameTextStyle: { color: tk.axis },
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: rows.map((r) => r.label),
      axisLine: { lineStyle: { color: tk.grid } },
      axisTick: { show: false },
      axisLabel: { color: tk.text, width: narrow ? 110 : 200, overflow: 'break' },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((r) => cho(r.value)),
        barMaxWidth: 18,
        itemStyle: { color, borderRadius: [0, 4, 4, 0] },
        emphasis: { itemStyle: { opacity: 0.85 } },
        label: { show: true, position: 'right', color: tk.text, formatter: (p) => yen(p.value * 10000) },
      },
    ],
  }
}

export const hbarsHeight = (n) => n * 36 + 40
