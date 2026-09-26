<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ComingNext from '../components/ComingNext.vue'
import IndicatorTrend from '../components/IndicatorTrend.vue'
import RankBars from '../components/RankBars.vue'
import StatTile from '../components/StatTile.vue'
import { loadDataset } from '../data.js'
import { fy } from '../format.js'
import { locale, t, tm } from '../i18n.js'
import { MAIN_KEYS, fmtInd, isNum, label } from '../local.js'

const DEFAULT_CODE = '281000' // 神戸市

const route = useRoute()
const router = useRouter()
const data = ref(null)
const error = ref('')
const prefIndex = ref(27)
const code = ref(DEFAULT_CODE) // municipality code, or 'pref' for the prefecture itself
const rankKey = ref('fiscal_strength')
const narrow = ref(window.innerWidth < 640)
const onResize = () => (narrow.value = window.innerWidth < 640)

onMounted(async () => {
  window.addEventListener('resize', onResize)
  try {
    data.value = await loadDataset('local-indicators')
  } catch (e) {
    error.value = String(e)
    return
  }
  applyQuery(route.query)
})

function applyQuery(q) {
  if (!data.value) return
  if (typeof q.pref === 'string' && /^\d{2}$/.test(q.pref)) {
    prefIndex.value = Number(q.pref) - 1
    code.value = 'pref'
  } else if (typeof q.code === 'string' && data.value.municipalities[q.code]) {
    code.value = q.code
    prefIndex.value = data.value.municipalities[q.code][0]
  }
  if (typeof q.ind === 'string' && MAIN_KEYS.includes(q.ind)) rankKey.value = q.ind
}
// A shared link opened in the same tab changes only the query; apply it too.
watch(() => route.query, applyQuery)
onBeforeUnmount(() => window.removeEventListener('resize', onResize))

// Keep the URL in sync so a view can be shared.
watch([code, prefIndex, rankKey], () => {
  if (!data.value) return
  const query =
    code.value === 'pref'
      ? { pref: String(prefIndex.value + 1).padStart(2, '0'), ind: rankKey.value }
      : { code: code.value, ind: rankKey.value }
  router.replace({ query })
})

const years = computed(() => data.value?.years ?? [])
const last = computed(() => years.value.length - 1)
const meta = computed(() => Object.fromEntries((data.value?.indicators ?? []).map((m) => [m.key, m])))
const prefName = computed(() => data.value?.prefecture_names[prefIndex.value] ?? '')

// Municipalities in the chosen prefecture that exist in the latest year.
const options = computed(() => {
  if (!data.value) return []
  return Object.entries(data.value.municipalities)
    .filter(([, m]) => m[0] === prefIndex.value && isNum(m[3].fiscal_strength[last.value]))
    .map(([c, m]) => ({ code: c, name: m[1] }))
})

function onPrefChange() {
  // Default to the prefecture itself when switching prefectures.
  code.value = 'pref'
}

const isPref = computed(() => code.value === 'pref')
const entity = computed(() => {
  const d = data.value
  if (!d) return null
  if (isPref.value) {
    const [name, values] = d.prefectures[prefIndex.value]
    return { name, values, designated: false }
  }
  const m = d.municipalities[code.value]
  return m ? { name: m[1], values: m[3], designated: m[2] === 1 } : null
})
const avgKey = computed(() => (isPref.value ? 'prefectural_average' : 'municipal_average'))
const avgLabel = computed(() => t(isPref.value ? 'local.avgPref' : 'local.avgMuni'))
const average = computed(() => data.value?.averages[avgKey.value] ?? {})

const tiles = computed(() => {
  if (!entity.value) return []
  return MAIN_KEYS.map((k) => {
    const m = meta.value[k]
    const v = entity.value.values[k]
    return {
      key: k,
      label: label(m),
      value: fmtInd(v[last.value], m),
      note: t('local.vsAvg', { label: avgLabel.value, v: fmtInd(average.value[k]?.[last.value], m) }),
      series: v.map((x) => (isNum(x) ? x : null)),
      trend: `${fy(years.value[0])}〜${fy(years.value[last.value])}`,
    }
  })
})

// Ranking within the prefecture (municipalities), or across prefectures.
const muniRows = computed(() => {
  if (!data.value) return []
  return Object.entries(data.value.municipalities)
    .filter(([, m]) => m[0] === prefIndex.value && m[3].fiscal_strength[last.value] != null)
    .map(([c, m]) => ({ name: m[1], value: m[3][rankKey.value][last.value], highlight: c === code.value }))
})
const prefRows = computed(() =>
  (data.value?.prefectures ?? []).map(([name, v], i) => ({
    name,
    value: v[rankKey.value][last.value],
    highlight: i === prefIndex.value,
  })),
)
const lastYear = computed(() => fy(years.value[last.value] ?? 0))
</script>

<template>
  <h1>{{ t('local.title') }}</h1>
  <p class="muted">{{ t('local.intro') }}</p>
  <p v-if="error" class="muted">{{ error }}</p>

  <template v-if="data && entity">
    <div class="controls">
      <label>
        {{ t('local.prefecture') }}
        <select v-model.number="prefIndex" @change="onPrefChange">
          <option v-for="(p, i) in data.prefecture_names" :key="p" :value="i">{{ p }}</option>
        </select>
      </label>
      <label>
        {{ t('local.municipality') }}
        <select v-model="code">
          <option value="pref">{{ prefName }}{{ t('local.prefOnly') }}</option>
          <option v-for="o in options" :key="o.code" :value="o.code">{{ o.name }}</option>
        </select>
      </label>
    </div>

    <h2 class="section">
      {{ t('local.latestTitle', { name: entity.name, year: lastYear }) }}
      <span v-if="entity.designated" class="badge">{{ t('local.designated') }}</span>
    </h2>
    <div class="tiles">
      <StatTile
        v-for="tile in tiles"
        :key="tile.key"
        :label="tile.label"
        :value="tile.value"
        :note="tile.note"
        :series="tile.series"
        :trend-label="tile.trend"
      />
    </div>
    <p class="caveat muted">{{ t('local.note') }}</p>

    <h2 class="section">{{ t('local.trendTitle') }}</h2>
    <p class="muted sub">{{ t('local.trendSub', { avg: avgLabel }) }}</p>
    <div class="grid two">
      <IndicatorTrend
        v-for="k in MAIN_KEYS"
        :key="`${code}-${prefIndex}-${k}`"
        :meta="meta[k]"
        :years="years"
        :name="entity.name"
        :values="entity.values[k]"
        :average="average[k]"
        :average-label="avgLabel"
        :is-prefecture="isPref"
        :is-designated="entity.designated"
        :narrow="narrow"
      />
    </div>

    <h2 class="section">{{ t('local.compareTitle') }}</h2>
    <div class="controls inline">
      <label>
        {{ t('local.indicator') }}
        <select v-model="rankKey">
          <option v-for="k in MAIN_KEYS" :key="k" :value="k">{{ label(meta[k]) }}</option>
        </select>
      </label>
    </div>
    <div class="grid two rank-grid">
      <div class="scroll">
        <RankBars
          :title="t('local.rankPref', { pref: prefName, year: lastYear })"
          :subtitle="t('local.rankSub')"
          :meta="meta[rankKey]"
          :rows="muniRows"
          :average="data.averages.municipal_average[rankKey][last]"
          :average-label="t('local.avgMuni')"
          :narrow="narrow"
        />
      </div>
      <div class="scroll">
        <RankBars
          :title="t('local.rankAll', { year: lastYear })"
          :subtitle="t('local.rankSub')"
          :meta="meta[rankKey]"
          :rows="prefRows"
          :average="data.averages.prefectural_average[rankKey][last]"
          :average-label="t('local.avgPref')"
          :narrow="narrow"
        />
      </div>
    </div>
    <p class="source muted">
      {{ t('source') }}:
      <a :href="data.source.url" target="_blank" rel="noopener">
        {{ locale === 'ja' ? data.source.publisher : data.source.publisher_en }}「{{ data.source.title }}」</a>
      （{{ t('processed') }}）
    </p>
  </template>

  <ComingNext :title="t('local.comingTitle')" :items="tm('local.coming')" />
</template>

<style scoped>
.controls { display: flex; flex-wrap: wrap; gap: 16px; align-items: center; margin: 16px -16px 0; padding: 10px 16px; position: sticky; top: 0; z-index: 5; background: color-mix(in srgb, var(--bg) 92%, transparent); backdrop-filter: blur(6px); border-bottom: 1px solid var(--border); }
.controls.inline { position: static; margin: 0 0 12px; padding: 0; border: 0; background: none; backdrop-filter: none; }
.controls select { margin-left: 8px; font: inherit; padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border); background: var(--surface); color: var(--text); max-width: 60vw; }
.section { margin: 2rem 0 0.75rem; font-size: 1.25rem; }
.sub { margin: -0.5rem 0 0; font-size: 0.9rem; }
.badge { font-size: 0.75rem; font-weight: 500; border: 1px solid var(--border); border-radius: 999px; padding: 2px 8px; margin-left: 8px; vertical-align: middle; color: var(--muted); }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); gap: 12px; }
.caveat { font-size: 0.8rem; margin: 8px 0 0; }
.grid.two { margin-top: 12px; }
.rank-grid { align-items: start; }
.scroll { max-height: 720px; overflow-y: auto; border-radius: var(--radius); }
.source { font-size: 0.8rem; }
</style>
