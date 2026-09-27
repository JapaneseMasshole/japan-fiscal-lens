// Shared ECharts option builders, so every chart follows the same mark specs:
// 2px lines, >=8px markers with a surface ring, <=18px bars with 4px rounded data-ends,
// hairline solid grid, text in text tokens (never the series color).
import echarts from './echarts.js'
import { cho, fy, pct, per100, perPerson, yen } from './format.js'
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

// Single-value items [{label, value, note?}] → rows sorted by size; items under 2% of
// `total` fold into "Other (n items)" with their names kept for the tooltip.
export function foldItems(items, total) {
  const big = []
  const small = []
  for (const it of items) (Math.abs(it.value) / total >= OTHER_THRESHOLD ? big : small).push(it)
  const rows = [...big].sort((a, b) => b.value - a.value)
  if (small.length > 1) {
    rows.push({
      label: t('national.other', { n: small.length }),
      value: small.reduce((s, it) => s + it.value, 0),
      members: small.map((it) => it.label),
    })
  } else rows.push(...small)
  return rows
}

// Tooltip for one breakdown item: amount, share and, with `persons`, the amount per person;
// plus the item's note and the members folded into "Other".
function breakdownTip(rows, total, persons) {
  return (p) => {
    const r = rows[p.dataIndex]
    const wrap = document.createElement('div')
    const v = document.createElement('strong')
    v.textContent = r.label
    const a = document.createElement('div')
    a.textContent = `${yen(r.value)} · ${t('national.share')} ${pct(r.value / total)}`
    wrap.append(v, a)
    if (persons) {
      const pp = document.createElement('div')
      pp.textContent = t('budget.perPersonShort', { v: perPerson(r.value, persons) })
      wrap.append(pp)
    }
    for (const extra of [r.note, r.members?.join(locale.value === 'ja' ? '、' : ', ')]) {
      if (!extra) continue
      const m = document.createElement('div')
      m.style.cssText = 'max-width:260px;white-space:normal;font-size:12px;opacity:.8'
      m.textContent = extra
      wrap.append(m)
    }
    return wrap
  }
}

// Horizontal bars for one breakdown. mode 'amount' plots 兆円; mode 'per100' plots yen out of
// every ¥100 of `total`, so two breakdowns of different totals can share one axis honestly.
export function breakdownBars(tk, rows, total, color, { mode = 'amount', max = null, narrow = false, persons = null } = {}) {
  const x = (v) => (mode === 'per100' ? (v / total) * 100 : cho(v))
  return {
    ...base(tk),
    grid: { left: 8, right: mode === 'per100' ? 56 : 72, top: 8, bottom: 8, containLabel: true },
    tooltip: { ...base(tk).tooltip, trigger: 'item', formatter: breakdownTip(rows, total, persons) },
    xAxis: {
      type: 'value',
      min: 0,
      max,
      axisLabel: { color: tk.axis, formatter: (v) => v.toLocaleString(), hideOverlap: true },
      splitLine: { lineStyle: { color: tk.grid } },
      name: mode === 'per100' ? (locale.value === 'ja' ? '円' : '¥') : unitLabel(),
      nameLocation: 'end',
      nameTextStyle: { color: tk.axis },
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: rows.map((r) => r.label),
      axisLine: { lineStyle: { color: tk.grid } },
      axisTick: { show: false },
      axisLabel: { color: tk.text, width: narrow ? 104 : 190, overflow: 'break', lineHeight: 16 },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((r) => x(r.value)),
        barMaxWidth: 18,
        itemStyle: { color, borderRadius: [0, 4, 4, 0] },
        emphasis: { itemStyle: { opacity: 0.85 } },
        label: {
          show: true,
          position: 'right',
          color: tk.text,
          formatter: (p) => (mode === 'per100' ? per100(rows[p.dataIndex].value, total) : yen(rows[p.dataIndex].value)),
        },
      },
    ],
  }
}

// The same breakdown as a pie (share of the whole). One hue, as in the bars: slices step
// lighter by rank and are separated by surface-colored gaps; "Other" is the context gray.
// Labels sit at the chart edges and carry the share (or yen out of ¥100 in 'per100' mode),
// so no value lives only in the tooltip. Only for breakdowns with no negative items.
// Blend two CSS colors: w = 0 gives `a`, w = 1 gives `b`. Solid colors rather than
// opacity, because ECharts fades a slice's label along with the slice.
const mix = (a, b, w) => echarts.color.lerp(w, [a, b])

export function breakdownPie(tk, rows, total, color, { mode = 'amount', narrow = false, persons = null } = {}) {
  const ranked = rows.filter((r) => !r.members).length
  const step = ranked > 1 ? 0.55 / (ranked - 1) : 0
  return {
    ...base(tk),
    tooltip: { ...base(tk).tooltip, trigger: 'item', formatter: breakdownTip(rows, total, persons) },
    series: [
      {
        type: 'pie',
        radius: narrow ? '46%' : '62%',
        center: ['50%', '50%'],
        startAngle: 90,
        clockwise: true,
        data: rows.map((r, i) => ({
          name: r.label,
          value: r.value,
          itemStyle: { color: r.members ? tk.context : mix(color, tk.surface, i * step) },
        })),
        itemStyle: { borderColor: tk.surface, borderWidth: 2 },
        emphasis: { scale: false, itemStyle: { opacity: 0.85 } },
        label: {
          color: tk.text,
          fontSize: narrow ? 11 : 12,
          lineHeight: narrow ? 14 : 16,
          width: narrow ? 100 : 170,
          overflow: 'break',
          alignTo: 'edge',
          edgeDistance: 4,
          formatter: (p) => {
            const r = rows[p.dataIndex]
            return `${r.label}\n${mode === 'per100' ? per100(r.value, total) : pct(r.value / total)}`
          },
        },
        labelLine: { length: 8, length2: 6, lineStyle: { color: tk.axis, width: 1 } },
      },
    ],
  }
}

// Shared axis maximum for charts compared side by side (rounded up to a clean step).
export function sharedMax(values, step) {
  return Math.ceil(Math.max(...values) / step) * step
}
