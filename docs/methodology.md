# Methodology / 方法

This page explains how every number on the site is produced. If a chart and this page disagree, the chart is wrong. Please open an issue.

## 1. Two kinds of government accounts

Japanese governments publish two different sets of figures, and news coverage often mixes them up.

| | Cash basis (現金主義) | Accrual basis (発生主義) |
|---|---|---|
| National | 一般会計 決算: tax revenue, bond issuance, spending | 国の財務書類: balance sheet, operating cost, cash flow by category |
| Local | 決算カード, 地方財政状況調査 | 統一的な基準による財務書類 |
| Answers | "How much came in and went out this year?" | "What does the government own and owe, and what did this year really cost?" |

The accrual statements are the ones closest to a company's balance sheet, income statement and cash flow statement. The site labels which basis each chart uses.

## 2. Corporate statements vs. government statements

| Company | National government (国) | Local government (地方) |
|---|---|---|
| Balance sheet | 貸借対照表 | 貸借対照表 |
| Income statement | 業務費用計算書 (costs only; taxes are not treated as "sales") | 行政コスト計算書 |
| Statement of changes in equity | 資産・負債差額増減計算書 | 純資産変動計算書 |
| Cash flow statement | 区分別収支計算書 | 資金収支計算書 |

Governments do not "earn" taxes the way a company earns sales, so there is no profit line. Tax revenue appears in the change-in-net-assets statement instead. The site says this plainly rather than forcing a corporate "profit" figure.

## 3. Scope choices that change the numbers

- **合算 vs. 連結 (national):** 合算 covers the general and special accounts. 連結 also includes related public entities (independent administrative agencies and others). The site shows 合算 by default and lets readers switch.
- **Gross vs. net debt:** gross debt ignores assets; net debt subtracts financial assets. Both are shown, side by side.
- **Central government vs. general government:** the 国の財務書類 do not include local governments or social security funds. International comparisons (IMF, OECD) usually use general government, so they are not directly comparable with these statements.

## 4. Processing rules

1. Original files are stored unedited in `data/raw/<source-id>/fy<year>/`, with a `manifest.json` recording the URL, SHA-256 hash and fetch time.
2. Units are unified to **億円 (100 million yen)**. Display may convert to 兆円.
3. Fiscal years are April–March, labelled by starting year (FY2024 = 令和6年度 = April 2024 – March 2025).
4. Derived figures (per-capita, % of GDP, inflation-adjusted) state their denominator's source and year.
5. Validation checks run on every change, e.g. assets = liabilities + net assets, and components sum to reported totals.

## 5. What this site does not do

- No forecasts, projections or scenarios.
- No judgement words ("crisis", "safe") in chart titles or labels.
- No selective time ranges: charts default to the full available history.
