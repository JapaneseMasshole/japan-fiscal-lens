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
