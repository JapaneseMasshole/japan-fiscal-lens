// Helpers for the local-government indicators dataset (local-indicators.json).
import { locale, t } from './i18n.js'

export const NC = 'nc' // 将来負担比率 not calculated (available funds exceed the burden)
export const MAIN_KEYS = ['fiscal_strength', 'current_balance_ratio', 'real_debt_service_ratio', 'future_burden_ratio']

export function label(meta) {
  return locale.value === 'ja' ? meta.ja : meta.en
}

export function desc(meta) {
  return locale.value === 'ja' ? meta.desc_ja : meta.desc_en
}

export function fmtInd(v, meta) {
  if (v === NC) return t('local.nc')
  if (v == null) return '—'
  return `${v.toFixed(meta.digits)}${meta.unit}`
}

export const isNum = (v) => typeof v === 'number' && Number.isFinite(v)

// Thresholds that legally apply to this kind of government.
export function thresholdsFor(meta, { isPrefecture = false, isDesignated = false } = {}) {
  return (meta.thresholds ?? []).filter((th) => {
    if (th.applies === 'all') return true
    if (th.applies === 'municipality') return !isPrefecture && !isDesignated
    if (th.applies === 'prefecture_or_designated') return isPrefecture || isDesignated
    return false
  })
}

export function thresholdLabel(th) {
  return `${locale.value === 'ja' ? th.ja : th.en} ${th.value}%`
}
