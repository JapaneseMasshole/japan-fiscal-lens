<script setup>
// One breakdown (e.g. 歳出 by 主要経費): sorted bars, publisher notes, source, and a table
// of every item with amount, share and per-person figures (folded items listed in full).
import { computed } from 'vue'
import ChartCard from './ChartCard.vue'
import { breakdownBars, foldItems } from '../charts.js'
import { cho, pct, perPerson } from '../format.js'
import { locale, t } from '../i18n.js'
import { isDark, tokens } from '../theme.js'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  items: { type: Array, required: true }, // [{ label, value (億円), note? }]
  total: { type: Number, required: true }, // 億円; shares are of this total
  totalLabel: { type: String, default: '' },
  colorSlot: { type: Number, default: 0 }, // categorical slot: 0 = funding (blue), 1 = spending (orange)
  mode: { type: String, default: 'amount' }, // 'amount' (兆円) | 'per100' (yen out of ¥100)
  max: { type: Number, default: null }, // shared axis maximum, when compared side by side
  persons: { type: Number, default: null },
  personsNote: { type: String, default: '' },
  notes: { type: Array, default: () => [] }, // strings shown under the chart
  source: { type: Object, default: null },
  narrow: Boolean,
})

const rows = computed(() => foldItems(props.items, props.total))
const option = computed(() => {
  void isDark.value
  const tk = tokens()
  return breakdownBars(tk, rows.value, props.total, tk.series[props.colorSlot], {
    mode: props.mode,
    max: props.max,
    narrow: props.narrow,
    persons: props.persons,
  })
})
const height = computed(() => rows.value.length * (props.narrow ? 44 : 36) + 40)
const num = (oku) =>
  cho(oku).toLocaleString(locale.value === 'ja' ? 'ja-JP' : 'en-US', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
const tableRows = computed(() => [...props.items].sort((a, b) => b.value - a.value))
</script>

<template>
  <ChartCard :title="title" :subtitle="subtitle" :option="option" :source="source" :height="height">
    <p v-for="n in notes" :key="n" class="note">{{ n }}</p>
    <p v-if="persons && personsNote" class="note">{{ personsNote }}</p>
    <details class="table">
      <summary>{{ t('budget.tableView') }}</summary>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">{{ t('national.item') }}</th>
              <th scope="col">{{ t('budget.colAmount') }}</th>
              <th scope="col">{{ t('national.share') }}</th>
              <th v-if="persons" scope="col">{{ t('budget.colPerPerson') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in tableRows" :key="r.label">
              <th scope="row">{{ r.label }}</th>
              <td>{{ num(r.value) }}</td>
              <td>{{ pct(r.value / total) }}</td>
              <td v-if="persons">{{ perPerson(r.value, persons) }}</td>
            </tr>
            <tr v-if="totalLabel" class="total">
              <th scope="row">{{ totalLabel }}</th>
              <td>{{ num(total) }}</td>
              <td>100.0%</td>
              <td v-if="persons">{{ perPerson(total, persons) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </details>
  </ChartCard>
</template>

<style scoped>
.note { font-size: 0.85rem; margin: 8px 0 0; color: var(--muted); }
.table { margin-top: 12px; font-size: 0.85rem; }
.table summary { cursor: pointer; color: var(--accent); }
.table-wrap { overflow-x: auto; margin-top: 8px; }
table { border-collapse: collapse; min-width: 100%; }
th, td { padding: 4px 8px; border-bottom: 1px solid var(--border); white-space: nowrap; }
td { text-align: right; font-variant-numeric: tabular-nums; }
thead th { text-align: right; color: var(--muted); font-weight: 500; }
thead th:first-child, tbody th { text-align: left; font-weight: 400; }
tr.total th, tr.total td { font-weight: 700; }
</style>
