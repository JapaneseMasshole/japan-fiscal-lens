<script setup>
// Collapsible "view as a table" for any dataset: rows × fiscal years, values in 兆円.
import { cho, fy } from '../format.js'
import { locale, t } from '../i18n.js'
import { unitLabel } from '../charts.js'

defineProps({
  years: { type: Array, required: true },
  rows: { type: Array, required: true }, // { label, values, level?, total?, heading? }
})

const fmt = (v) =>
  v == null || !Number.isFinite(v)
    ? '—'
    : cho(v).toLocaleString(locale.value === 'ja' ? 'ja-JP' : 'en-US', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      })
</script>

<template>
  <details class="table-card">
    <summary>{{ t('national.table') }}（{{ unitLabel() }}）</summary>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">{{ t('national.item') }}</th>
            <th v-for="y in years" :key="y" scope="col">{{ fy(y) }}</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(r, i) in rows" :key="i">
            <tr v-if="r.heading" class="heading">
              <th scope="rowgroup" :colspan="years.length + 1">{{ r.heading }}</th>
            </tr>
            <tr :class="{ total: r.total }">
              <th scope="row" :style="{ paddingLeft: `${8 + (r.level || 0) * 16}px` }">{{ r.label }}</th>
              <td v-for="(v, j) in r.values" :key="j">{{ fmt(v) }}</td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </details>
</template>

<style scoped>
.table-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 16px; }
.table-card summary { cursor: pointer; font-weight: 600; }
.table-wrap { overflow-x: auto; margin-top: 12px; }
table { border-collapse: collapse; font-size: 0.85rem; min-width: 100%; }
th, td { padding: 4px 8px; border-bottom: 1px solid var(--border); white-space: nowrap; }
td { text-align: right; font-variant-numeric: tabular-nums; }
thead th { text-align: right; color: var(--muted); font-weight: 500; }
thead th:first-child, tbody th { text-align: left; font-weight: 400; position: sticky; left: 0; background: var(--surface); }
tr.total th, tr.total td { font-weight: 700; }
tr.heading th { font-weight: 600; color: var(--muted); padding-top: 12px; }
</style>
