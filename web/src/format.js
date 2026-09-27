import { locale } from './i18n.js'

// Data is stored in 億円 (100 million yen). Display in 兆円 (trillion yen).
export function cho(oku) {
  return oku / 10000
}

export function yen(oku, digits = 1) {
  const n = cho(oku)
  const s = n.toLocaleString(locale.value === 'ja' ? 'ja-JP' : 'en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
  return locale.value === 'ja' ? `${s}兆円` : `¥${s}tn`
}

export function fy(year) {
  return locale.value === 'ja' ? `${year}年度` : `FY${year}`
}

export function pct(x) {
  return `${(x * 100).toFixed(1)}%`
}

// Amount per person: 億円 total ÷ population, shown as 万円 (ja) or yen (en).
export function perPerson(oku, persons) {
  const yenPer = (oku * 1e8) / persons
  if (locale.value === 'ja') {
    return `${(yenPer / 10000).toLocaleString('ja-JP', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}万円`
  }
  return `¥${Math.round(yenPer / 1000).toLocaleString('en-US')}k`
}

// Share of a total expressed as yen out of every ¥100 (31.9 → 「31.9円」 / "¥31.9").
export function per100(value, total) {
  const s = ((value / total) * 100).toFixed(1)
  return locale.value === 'ja' ? `${s}円` : `¥${s}`
}
