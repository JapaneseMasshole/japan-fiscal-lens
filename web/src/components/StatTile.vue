<script setup>
// Stat tile: label · value · optional note · sparkline of the full history (latest point marked).
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  note: { type: String, default: '' },
  trendLabel: { type: String, default: '' },
  series: { type: Array, default: () => [] }, // numbers, oldest → newest
  color: { type: String, default: 'var(--viz-series-1)' },
})

const W = 160
const H = 40
const PAD = 5
const path = computed(() => {
  const s = props.series.filter((v) => v != null)
  if (s.length < 2) return null
  // Zero-anchored so the slope is honest (a free-floating range exaggerates small changes).
  const min = Math.min(0, ...s)
  const max = Math.max(0, ...s)
  const span = max - min || 1
  const pts = s.map((v, i) => [
    PAD + (i * (W - 2 * PAD)) / (s.length - 1),
    H - PAD - ((v - min) / span) * (H - 2 * PAD),
  ])
  return { d: pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join(''), end: pts.at(-1) }
})
</script>

<template>
  <div class="tile">
    <div class="label">{{ label }}</div>
    <div class="value">{{ value }}</div>
    <div v-if="note" class="note">{{ note }}</div>
    <svg v-if="path" :viewBox="`0 0 ${W} ${H}`" class="spark" role="img" :aria-label="trendLabel">
      <path :d="path.d" fill="none" :stroke="color" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />
      <circle :cx="path.end[0]" :cy="path.end[1]" r="4" :fill="color" stroke="var(--surface)" stroke-width="2" />
    </svg>
    <div v-if="trendLabel" class="trend">{{ trendLabel }}</div>
  </div>
</template>

<style scoped>
.tile { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 16px 12px; display: flex; flex-direction: column; min-width: 0; }
.label { color: var(--muted); font-size: 0.9rem; }
.value { font-size: 1.9rem; font-weight: 600; line-height: 1.25; margin-top: 4px; letter-spacing: -0.01em; }
.note { color: var(--muted); font-size: 0.85rem; }
.spark { width: 100%; height: 40px; margin-top: auto; padding-top: 8px; overflow: visible; }
.trend { color: var(--muted); font-size: 0.75rem; }
</style>
