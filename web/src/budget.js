// Shape national-budget.json and social-security.json into chart items, so the home page
// and the National page read the same numbers the same way.
import { ref } from 'vue'
import { loadDataset } from './data.js'
import { fy, yen } from './format.js'
import { locale, t } from './i18n.js'

export const budget = ref(null)
export const social = ref(null)

let loading = null
export function loadBudget() {
  loading ??= Promise.all([loadDataset('national-budget'), loadDataset('social-security')]).then(
    ([b, s]) => {
      budget.value = b
      social.value = s
    },
  )
  return loading
}

const name = (line) => (locale.value === 'ja' ? line.ja : line.en)
const item = (line, extra = {}) => ({ label: name(line), value: line.value, ...extra })
export const note = (d, key) => d?.notes?.[key]?.[locale.value] ?? ''

// 歳出 by 主要経費. The 文教 line carries its うち科学技術振興費 as a tooltip note.
export function spendingItems(b) {
  return b.expenditure.map((l) =>
    l.item === '文教及び科学振興費'
      ? item(l, { note: `${name(b.science)} ${yen(b.science.value)}` })
      : item(l),
  )
}

// 歳入 as funding sources: each tax, the two kinds of bonds, other revenue.
export function fundingItems(b) {
  const bond = (l) => ({ label: `${t('budget.bondPrefix')}${name(l)}`, value: l.value })
  return [
    ...b.tax.map((l) => item(l)),
    bond(b.revenue.deficit_bonds),
    bond(b.revenue.construction_bonds),
    item(b.revenue.other),
  ]
}

export const socialBudgetItems = (b) => b.social_security.map((l) => item(l))
export const taxItems = (b) => b.tax.map((l) => item(l))

// IPSS: one table's items for its latest year (合計 excluded; nested items per `pick`).
export function ssItems(s, table, pick) {
  const tb = s.tables[table]
  const i = tb.years.indexOf(s.latest_year)
  return tb.items
    .filter((it) => pick.includes(it.ja))
    .map((it) => ({ label: locale.value === 'ja' ? it.ja : it.en, value: it.values[i], ja: it.ja }))
}
export function ssValue(s, table, ja) {
  const tb = s.tables[table]
  return tb.items.find((it) => it.ja === ja).values[tb.years.indexOf(s.latest_year)]
}

export const budgetYear = (b) =>
  locale.value === 'ja' ? `令和${b.fiscal_year - 2018}年度（${fy(b.fiscal_year)}）` : fy(b.fiscal_year)

export function populationNote(pop) {
  const [y, m, d] = pop.as_of.split('-').map(Number)
  const date =
    locale.value === 'ja'
      ? `${y}年${m}月${d}日`
      : new Date(y, m - 1, d).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
  return t('budget.perPersonNote', {
    date,
    n: (pop.persons / 1e4).toLocaleString(locale.value === 'ja' ? 'ja-JP' : 'en-US', { maximumFractionDigits: 0 }),
    persons: pop.persons.toLocaleString('en-US'),
  })
}

