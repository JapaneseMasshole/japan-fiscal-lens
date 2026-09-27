<script setup>
// One breakdown (e.g. 歳出 by 主要経費): sorted bars or a pie (viewer's choice, shared by
// every breakdown), publisher notes, source, and a table of every item with amount, share
// and per-person figures (folded items listed in full).
import { computed } from 'vue'
import ChartCard from './ChartCard.vue'
import { breakdownBars, breakdownPie, foldItems } from '../charts.js'
import { cho, pct, perPerson } from '../format.js'
import { locale, t } from '../i18n.js'
import { breakdownView } from '../prefs.js'
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
// A pie shows parts of a whole, so it is offered only when no item is negative.
const canPie = computed(() => props.items.every((it) => it.value >= 0))
const pie = computed(() => canPie.value && breakdownView.value === 'pie')
const option = computed(() => {
  void isDark.value
  const tk = tokens()
  const opts = { mode: props.mode, max: props.max, narrow: props.narrow, persons: props.persons }
  return (pie.value ? breakdownPie : breakdownBars)(tk, rows.value, props.total, tk.series[props.colorSlot], opts)
})
const height = computed(() =>
  pie.value ? (props.narrow ? 300 : 360) : rows.value.length * (props.narrow ? 44 : 36) + 40,
)
const views = [
  ['bars', 'budget.viewBars'],
  ['pie', 'budget.viewPie'],
]
const num = (oku) =>
  cho(oku).toLocaleString(locale.value === 'ja' ? 'ja-JP' : 'en-US', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
const tableRows = computed(() => [...props.items].sort((a, b) => b.value - a.value))
</script>

<template>
  <ChartCard :title="title" :subtitle="subtitle" :option="option" :source="source" :height="height">
    <template v-if="canPie" #actions>
      <div class="views" role="group" :aria-label="t('budget.viewLabel')">
        <button
          v-for="[v, key] in views"
          :key="v"
          type="button"
          :aria-pressed="breakdownView === v"
          @click="breakdownView = v"
        >
          {{ t(key) }}
        </button>
      </div>
    </template>
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
.views { display: inline-flex; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; flex: none; }
.views button { font: inherit; font-size: 0.8rem; padding: 2px 10px; border: 0; background: transparent; color: var(--muted); cursor: pointer; }
.views button + button { border-left: 1px solid var(--border); }
.views button[aria-pressed='true'] { background: var(--border); color: var(--text); font-weight: 600; }
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
