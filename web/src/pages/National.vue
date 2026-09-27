<script setup>
// The national budget: what it pays for (歳出), how it is funded (歳入), and social security
// as a whole (benefits and who pays), from official data only.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import BreakdownCard from '../components/BreakdownCard.vue'
import ComingNext from '../components/ComingNext.vue'
import StatTile from '../components/StatTile.vue'
import {
  budget,
  budgetYear,
  loadBudget,
  note,
  populationNote,
  social,
  socialBudgetItems,
  spendingItems,
  ssItems,
  ssValue,
  taxItems,
} from '../budget.js'
import { sharedMax } from '../charts.js'
import { fy, pct, perPerson, yen } from '../format.js'
import { locale, t, tm } from '../i18n.js'

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
const ssYear = computed(() => (s.value ? fy(s.value.latest_year) : ''))
const persons = computed(() => b.value?.population.persons)

const revenueTiles = computed(() => {
  const d = b.value
  if (!d) return []
  const r = d.revenue
  const share = (v) => t('budget.fundShare', { v: pct(v / d.total) })
  return [
    { label: t('budget.fundTaxes'), value: yen(r.taxes.value), note: share(r.taxes.value) },
    {
      label: t('budget.fundBonds'),
      value: yen(r.bonds.value),
      note: `${share(r.bonds.value)}（${t('budget.bondsSplit', {
        a: yen(r.construction_bonds.value),
        b: yen(r.deficit_bonds.value),
      })}）`,
    },
    { label: t('budget.fundOther'), value: yen(r.other.value), note: share(r.other.value) },
  ]
})

const debtService = computed(() => b.value?.expenditure.find((l) => l.item === '国債費'))
const ssBudgetTotal = computed(() => b.value?.expenditure.find((l) => l.item === '社会保障関係費'))

// IPSS: benefits and revenue share one axis (both in 兆円).
const ssBenefits = computed(() => {
  if (!s.value) return []
  const care = ssValue(s.value, 'benefit_by_category', '介護対策')
  return ssItems(s.value, 'benefit_by_category', ['医療', '年金', '福祉その他']).map((it) =>
    it.ja === '福祉その他' ? { ...it, note: t('budget.ssBenefitCare', { v: yen(care) }) } : it,
  )
})
const ssRevenue = computed(() =>
  s.value
    ? ssItems(s.value, 'revenue', ['被保険者拠出', '事業主拠出', '国庫負担', '他の公費負担', '資産収入', 'その他'])
    : [],
)
const ssMax = computed(() =>
  s.value ? sharedMax([...ssBenefits.value, ...ssRevenue.value].map((it) => it.value / 10000), 10) : null,
)
const ssTiles = computed(() => {
  const d = s.value
  if (!d) return []
  const v = (table, ja) => ssValue(d, table, ja)
  const y = ssYear.value
  const pp = (x) => t('budget.perPersonShort', { v: perPerson(x, d.population.persons) })
  return [
    { label: t('budget.ssBenefitTotal', { year: y }), value: yen(v('benefit_by_category', '合計')), note: pp(v('benefit_by_category', '合計')) },
    {
      label: t('budget.ssPremiums', { year: y }),
      value: yen(v('revenue', '社会保険料')),
      note: t('budget.ssPremiumsNote', { a: yen(v('revenue', '被保険者拠出')), b: yen(v('revenue', '事業主拠出')) }),
    },
    {
      label: t('budget.ssPublic', { year: y }),
      value: yen(v('revenue', '公費負担')),
      note: t('budget.ssPublicNote', { a: yen(v('revenue', '国庫負担')), b: yen(v('revenue', '他の公費負担')) }),
    },
  ]
})
</script>

<template>
  <h1>{{ t('budget.title') }}</h1>
  <p v-if="b" class="muted intro">{{ t('budget.intro', { year }) }}</p>

  <template v-if="b">
    <!-- 歳出 -->
    <h2 id="spend" class="section">{{ t('budget.spendSection') }}</h2>
    <div class="grid one">
      <BreakdownCard
        :title="`${t('budget.spendTitle')}（${year}）`"
        :subtitle="t('budget.spendSub')"
        :items="spendingItems(b)"
        :total="b.total"
        :total-label="t('budget.spendTotal')"
        :color-slot="1"
        :persons="persons"
        :persons-note="populationNote(b.population)"
        :notes="[t('budget.stageNote'), note(b, 'public_works'), note(b, 'rounding')]"
        :source="b.source"
        :narrow="narrow"
      />
    </div>
    <div class="grid">
      <BreakdownCard
        :title="`${t('budget.ssBudgetTitle')}（${year}）`"
        :subtitle="t('budget.ssBudgetSub')"
        :items="socialBudgetItems(b)"
        :total="ssBudgetTotal.value"
        :total-label="t('budget.ssBudgetTotal')"
        :color-slot="1"
        :persons="persons"
        :notes="[note(b, 'social_security')]"
        :source="b.source"
        :narrow="narrow"
      />
      <section class="card">
        <h2>{{ t('budget.debtTitle') }}（{{ year }}）</h2>
        <div class="tiles two">
          <StatTile
            :label="t('budget.debtInterest')"
            :value="yen(b.debt_service.interest.value)"
            :note="t('budget.debtOf', { v: yen(debtService.value) })"
          />
          <StatTile
            :label="t('budget.debtRedemption')"
            :value="yen(b.debt_service.redemption.value)"
            :note="t('budget.debtOf', { v: yen(debtService.value) })"
          />
        </div>
        <p class="note">{{ note(b, 'debt_service') }}</p>
        <p class="source muted">
          {{ t('source') }}:
          <a :href="b.source.url" target="_blank" rel="noopener">
            {{ locale === 'ja' ? b.source.publisher : b.source.publisher_en }}「{{ b.source.title }}」</a>
          （{{ t('processed') }}）
        </p>
      </section>
    </div>

    <!-- 歳入 -->
    <h2 id="fund" class="section">{{ t('budget.fundSection') }}</h2>
    <div class="tiles three">
      <StatTile v-for="tile in revenueTiles" :key="tile.label" :label="tile.label" :value="tile.value" :note="tile.note" />
    </div>
    <div class="grid one">
      <BreakdownCard
        :title="`${t('budget.taxTitle')}（${year}）`"
        :subtitle="t('budget.taxSub')"
        :items="taxItems(b)"
        :total="b.revenue.taxes.value"
        :total-label="t('budget.taxTotal')"
        :color-slot="0"
        :persons="persons"
        :notes="[note(b, 'consumption_tax')]"
        :source="b.source"
        :narrow="narrow"
      />
    </div>
    <p v-if="b.supplementary_enacted" class="notice">{{ t('budget.supplementary') }}</p>
  </template>

  <!-- 社会保障の全体像 -->
  <template v-if="s">
    <h2 id="social" class="section">{{ t('budget.ssSection') }}</h2>
    <p class="muted intro">{{ t('budget.ssIntro', { year: ssYear }) }}</p>
    <div class="tiles three">
      <StatTile v-for="tile in ssTiles" :key="tile.label" :label="tile.label" :value="tile.value" :note="tile.note" />
    </div>
    <div class="grid">
      <BreakdownCard
        :title="t('budget.ssBenefitTitle', { year: ssYear })"
        :subtitle="t('budget.ssBenefitSub')"
        :items="ssBenefits"
        :total="ssValue(s, 'benefit_by_category', '合計')"
        :total-label="t('budget.ssBenefitTotal', { year: ssYear })"
        :color-slot="1"
        :max="ssMax"
        :persons="s.population.persons"
        :source="s.source"
        :narrow="narrow"
      />
      <BreakdownCard
        :title="t('budget.ssRevenueTitle', { year: ssYear })"
        :subtitle="t('budget.ssRevenueSub')"
        :items="ssRevenue"
        :total="ssValue(s, 'revenue', '合計')"
        :total-label="t('budget.ssRevenueTotal')"
        :color-slot="0"
        :max="ssMax"
        :persons="s.population.persons"
        :notes="[note(s, 'insured'), note(s, 'public'), note(s, 'income_from_capital'), note(s, 'revenue_vs_benefit')]"
        :source="s.source"
        :narrow="narrow"
      />
    </div>
    <p class="notice">{{ note(s, 'bridge') }}</p>
  </template>

  <RouterLink to="/statements" class="tile-link">
    <h2>{{ t('budget.statementsLink') }} →</h2>
    <p class="muted">{{ t('budget.statementsLinkSub') }}</p>
  </RouterLink>

  <ComingNext :title="t('national.comingTitle')" :intro="t('national.comingIntro')" :items="tm('national.coming')" />
</template>

<style scoped>
.section { margin: 2.5rem 0 0.75rem; font-size: 1.25rem; }
.intro { margin: 0 0 12px; max-width: 46rem; }
.grid.one { grid-template-columns: 1fr; }
.grid { margin: 16px 0; }
.tiles { display: grid; gap: 12px; margin: 12px 0; }
.tiles.three { grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); }
.tiles.two { grid-template-columns: repeat(auto-fit, minmax(min(100%, 160px), 1fr)); }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; min-width: 0; }
.card .tiles { margin: 0; }
.note { font-size: 0.85rem; margin: 8px 0 0; color: var(--muted); }
.source { font-size: 0.8rem; margin: 8px 0 0; }
.notice { font-size: 0.85rem; margin: 8px 0 16px; padding: 8px 12px; border-radius: 6px; background: var(--surface); border: 1px solid var(--border); }
.tile-link { display: block; text-decoration: none; color: inherit; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin: 32px 0 0; }
.tile-link:hover { border-color: var(--accent); }
.tile-link p { margin: 0; font-size: 0.9rem; }
</style>
