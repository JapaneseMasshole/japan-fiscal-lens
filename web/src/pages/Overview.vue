<script setup>
// Home: the national budget in one screen: the total, what ¥100 of it pays for, and how
// that ¥100 is raised (same scale), plus the size of social security as a whole.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import BreakdownCard from '../components/BreakdownCard.vue'
import StatTile from '../components/StatTile.vue'
import { budget, budgetYear, fundingItems, loadBudget, note, populationNote, social, spendingItems, ssValue } from '../budget.js'
import { foldItems, sharedMax } from '../charts.js'
import { fy, pct, perPerson, yen } from '../format.js'
import { locale, t } from '../i18n.js'

const narrow = ref(window.innerWidth < 640)
const onResize = () => (narrow.value = window.innerWidth < 640)
onMounted(() => {
  window.addEventListener('resize', onResize)
  loadBudget()
})
onBeforeUnmount(() => window.removeEventListener('resize', onResize))

const b = budget
const s = social
const year = computed(() => (b.value ? budgetYear(b.value) : ''))

const spend = computed(() => (b.value ? spendingItems(b.value) : []))
const fund = computed(() => (b.value ? fundingItems(b.value) : []))
// Both charts plot yen out of ¥100 on one axis, sized to the larger of the two.
const max100 = computed(() => {
  if (!b.value) return null
  const rows = [...foldItems(spend.value, b.value.total), ...foldItems(fund.value, b.value.total)]
  return sharedMax(rows.map((r) => (r.value / b.value.total) * 100), 10)
})

const tiles = computed(() => {
  const d = b.value
  if (!d) return []
  const line = (item) => d.expenditure.find((l) => l.item === item)
  const ss = line('社会保障関係費')
  const debt = line('国債費')
  const name = (l) => (locale.value === 'ja' ? l.ja : l.en)
  const share = (v) => t('budget.spendShare', { v: pct(v / d.total) })
  const out = [
    { label: name(ss), value: yen(ss.value), note: share(ss.value) },
    {
      label: name(debt),
      value: yen(debt.value),
      note: `${share(debt.value)} · ${t('budget.debtInterest')} ${yen(d.debt_service.interest.value)}`,
    },
    { label: t('budget.fundBonds'), value: yen(d.revenue.bonds.value), note: t('budget.fundShare', { v: pct(d.revenue.bonds.value / d.total) }) },
  ]
  if (s.value) {
    const total = ssValue(s.value, 'benefit_by_category', '合計')
    out.push({
      label: t('budget.ssBenefitTotal', { year: fy(s.value.latest_year) }),
      value: yen(total),
      note: t('budget.ssPremiumsNote', {
        a: yen(ssValue(s.value, 'revenue', '被保険者拠出')),
        b: yen(ssValue(s.value, 'revenue', '事業主拠出')),
      }),
    })
  }
  return out
})
</script>

<template>
  <section class="hero">
    <p class="tagline">{{ t('tagline') }}</p>
    <template v-if="b">
      <div class="hero-label">{{ t('budget.heroLabel', { year }) }}</div>
      <div class="hero-value">{{ yen(b.total) }}</div>
      <div class="hero-sub">{{ t('budget.perPerson', { v: perPerson(b.total, b.population.persons) }) }}</div>
    </template>
  </section>

  <div class="tiles">
    <StatTile v-for="tile in tiles" :key="tile.label" :label="tile.label" :value="tile.value" :note="tile.note" />
  </div>

  <div v-if="b" class="grid pair">
    <BreakdownCard
      :title="t('budget.spend100')"
      :subtitle="t('budget.pair100Sub')"
      :items="spend"
      :total="b.total"
      :total-label="t('budget.spendTotal')"
      :color-slot="1"
      mode="per100"
      :max="max100"
      :persons="b.population.persons"
      :source="b.source"
      :narrow="narrow"
    />
    <BreakdownCard
      :title="t('budget.fund100')"
      :subtitle="t('budget.pair100Sub')"
      :items="fund"
      :total="b.total"
      :total-label="t('budget.spendTotal')"
      :color-slot="0"
      mode="per100"
      :max="max100"
      :persons="b.population.persons"
      :notes="[note(b, 'consumption_tax')]"
      :source="b.source"
      :narrow="narrow"
    />
  </div>
  <p v-if="b" class="small muted">
    {{ t('budget.stageNote') }} {{ b.supplementary_enacted ? t('budget.supplementary') : '' }}
    {{ populationNote(b.population) }}
  </p>

  <div class="grid links">
    <RouterLink to="/national" class="tile-link">
      <h2>{{ t('budget.more') }}</h2>
      <p class="muted">{{ t('budget.spendSection') }} · {{ t('budget.fundSection') }} · {{ t('budget.ssSection') }}</p>
    </RouterLink>
    <RouterLink to="/statements" class="tile-link">
      <h2>{{ t('statements.title') }} →</h2>
      <p class="muted">{{ t('national.bs') }} · {{ t('national.costSection') }} · {{ t('national.cfSection') }}</p>
    </RouterLink>
  </div>
  <p class="small muted">{{ t('budget.disclaimer') }}</p>
</template>

<style scoped>
.hero { padding: 24px 0 8px; }
.tagline { font-size: 1.05rem; color: var(--muted); margin: 0 0 16px; }
.hero-label { color: var(--muted); font-size: 0.95rem; }
.hero-value { font-size: clamp(2.8rem, 9vw, 3.6rem); font-weight: 700; line-height: 1.1; letter-spacing: -0.02em; }
.hero-sub { font-size: 1.1rem; margin-top: 4px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); gap: 12px; margin-top: 16px; }
.grid.pair { margin: 24px 0 8px; }
.grid.links { margin: 24px 0 8px; }
.small { font-size: 0.8rem; margin: 8px 0 0; }
.tile-link { display: block; text-decoration: none; color: inherit; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }
.tile-link:hover { border-color: var(--accent); }
.tile-link p { margin: 0; font-size: 0.9rem; }
</style>
