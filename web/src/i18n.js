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

export function t(key) {
  return key.split('.').reduce((obj, k) => obj?.[k], messages[locale.value]) ?? key
}
