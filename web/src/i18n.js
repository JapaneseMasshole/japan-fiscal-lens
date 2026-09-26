import { ref } from 'vue'

// Minimal bilingual support. Japanese is the default audience.
export const locale = ref('ja')

const messages = {
  ja: {
    siteName: '財政レンズ',
    tagline: '国と地方自治体の財政を、公式データからグラフで分かりやすく。',
    nav: { overview: '概要', national: '国', local: '地方自治体', methodology: 'データと方法' },
    source: '出典',
    processed: '加工して作成',
    noData: 'データ準備中です。パイプラインが最初のデータを出力すると、ここにグラフが表示されます。',
    national: {
      title: '国の財政',
      bs: '貸借対照表（資産と負債）',
      cost: '業務費用計算書（1年間のコスト）',
      cf: '区分別収支計算書（お金の出入り）',
      debt: '国債の保有者',
      bsTrendTitle: '資産・負債・その差額の推移',
      bsTrendSub: '一般会計・特別会計の合算。各年度末（3月31日）時点。',
      assets: '資産合計',
      liabilities: '負債合計',
      netAssets: '資産・負債差額',
      compTitle: '内訳',
      assetsComp: '資産の内訳',
      liabilitiesComp: '負債の内訳',
      compSub: '資産と負債は同じ目盛りで表示しています。総額の2%未満の項目は「その他」にまとめています。',
      other: 'その他（{n}項目）',
      share: '構成比',
      year: '年度',
      table: '表で見る（全項目）',
      item: '項目',
      missing: '{year}：{reason}',
    },
    local: {
      title: '地方自治体の財政',
      intro: '都道府県・市区町村を選んで、統一的な基準による財務書類を比較できるようにする予定です。',
      bs: '貸借対照表',
      cost: '行政コスト計算書',
      cf: '資金収支計算書',
    },
    methodology: { title: 'データと方法' },
  },
  en: {
    siteName: 'Japan Fiscal Lens',
    tagline: "Japan's national and local public finances, visualized from official data.",
    nav: { overview: 'Overview', national: 'National', local: 'Local', methodology: 'Data & method' },
    source: 'Source',
    processed: 'processed by Japan Fiscal Lens',
    noData: 'Data coming soon. Charts appear here once the pipeline exports its first dataset.',
    national: {
      title: 'National government',
      bs: 'Balance sheet (assets and liabilities)',
      cost: 'Operating cost statement (cost of one year)',
      cf: 'Cash flow by category',
      debt: 'Who holds government bonds',
      bsTrendTitle: 'Assets, liabilities and the gap between them',
      bsTrendSub: 'General and special accounts combined. At each fiscal year end (March 31).',
      assets: 'Total assets',
      liabilities: 'Total liabilities',
      netAssets: 'Assets minus liabilities',
      compTitle: 'Breakdown',
      assetsComp: 'What the government owns',
      liabilitiesComp: 'What the government owes',
      compSub: 'Assets and liabilities share one scale. Items under 2% of the total are grouped as "Other".',
      other: 'Other ({n} items)',
      share: 'Share',
      year: 'Fiscal year',
      table: 'View as a table (all items)',
      item: 'Item',
      missing: '{year}: {reason}',
    },
    local: {
      title: 'Local governments',
      intro: 'Choose a prefecture or municipality to compare financial statements prepared under the unified standard (coming soon).',
      bs: 'Balance sheet',
      cost: 'Administrative cost statement',
      cf: 'Cash flow statement',
    },
    methodology: { title: 'Data & method' },
  },
}

export function t(key, vars = {}) {
  const msg = key.split('.').reduce((obj, k) => obj?.[k], messages[locale.value]) ?? key
  return msg.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? `{${k}}`)
}
