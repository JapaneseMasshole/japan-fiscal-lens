# Data dictionary

Schema for the files in `data/processed/` and `web/public/data/`. Fill this in as each dataset is added.

## Common columns (processed CSV)

| Column | Type | Description |
|---|---|---|
| `source_id` | string | id from `data/sources.yaml` |
| `level` | `national` \| `local` | government level |
| `entity_code` | string | `JP` for national; 6-digit 地方公共団体コード for local |
| `entity_name` | string | e.g. 国, 兵庫県, 神戸市 |
| `fiscal_year` | int | starting year, e.g. 2024 for 令和6年度 |
| `statement` | string | `balance_sheet`, `operating_cost`, `cash_flow`, … |
| `scope` | string | `gassan`, `ippan`, `renketsu` (national); `general`, `consolidated` (local) |
| `item_ja` | string | line item as written in the source |
| `item_en` | string | English translation |
| `category` | string | normalized category for charting |
| `value_oku_yen` | number | value in 億円 |

## `data/processed/national_balance_sheet.csv`

One row per fiscal year × balance-sheet line (MOF 国の財務書類, 合算).

| Column | Description |
|---|---|
| `scope` | `gassan` (general + special accounts) |
| `fiscal_year` | fiscal year whose end (March 31 of the next year) the figure describes |
| `column` | `current` (本会計年度) or `previous` (前会計年度) column of the source workbook |
| `source_file_year` | fiscal year of the workbook, read from its own date headers |
| `source_folder` | folder under `data/raw/mof-fs/` the workbook was read from |
| `section` | `assets`, `liabilities`, `net_assets` or `total` |
| `order` | line order within its block, as printed |
| `item_ja` / `item_en` | line name as printed / English translation |
| `level` | nesting depth from the Excel indent (0 = top level) |
| `parent_ja` | parent line for nested items, empty for top level |
| `is_total` | printed total line |
| `value_oku_yen` | value in 億円 (source is 百万円 ÷ 100) |

## `data/processed/national_budget.csv`

One row per budget table × line (MOF 一般会計予算, newest enacted year).

| Column | Description |
|---|---|
| `fiscal_year` | budget year, read from the PDF title (「令和８年度…」) |
| `statement` | `revenue`, `expenditure` (主要経費別), `tax` (税目別), `social_security` (社会保障関係費の内訳), `debt_service` (国債費の内訳) |
| `item_ja` | line name as printed, spaces removed (e.g. `⑴公債金`, `うち利払費`) |
| `value_oku_yen` | budget figure in 億円 (source unit) |
| `prev_oku_yen` | previous year's initial budget as printed in the same table; empty for 「－」 (no amount) |
| `order` | line order as printed |
| `file`, `page` | raw file under `data/raw/mof-budget/fy<year>/` and PDF page |

## `data/processed/social_security.csv`

One row per IPSS table × fiscal year × item (社会保障費用統計, full history).

| Column | Description |
|---|---|
| `table` | `benefit_by_category` (第８表), `benefit_by_function` (第13表), `revenue` (第14表, ILO standard) |
| `fiscal_year` | fiscal year |
| `item_ja` / `item_en` | column header as printed / English from the same table |
| `value_oku_yen` | 億円 |
| `order` | column order as printed (0 = 合計) |

Nested items: `介護対策` is part of `福祉その他`; `被保険者拠出` + `事業主拠出` = `社会保険料`; `国庫負担` + `他の公費負担` = `公費負担`.

## `web/public/data/national-budget.json`

`fiscal_year`, `total`, `expenditure[]`, `revenue{taxes, other, bonds, construction_bonds, deficit_bonds}`, `tax[]` (所得税 as one line, with `income_tax_parts`), `social_security[]`, `debt_service{redemption, interest}`, `science` (うち科学技術振興費). Each line is `{item, ja, en, value, prev}` in 億円. Also includes `enactment` (`as_proposed`), `supplementary_enacted`, `population{persons, as_of, source}` and `notes{…}` (publisher notes, ja/en).

## `web/public/data/social-security.json`

`tables.<table> = {years[], items[{ja, en, values[]}]}` for the three IPSS tables (values aligned with `years`, `null` where not published), plus `latest_year`, `population` and `notes`.

## Web JSON

Every file in `web/public/data/` must include a `source` object. The site refuses to draw a chart without one:

```json
{
  "id": "national-balance-sheet",
  "source": {
    "id": "mof-fs",
    "publisher": "財務省",
    "title": "国の財務書類",
    "url": "https://www.mof.go.jp/..."
  },
  "unit": "億円",
  "series": []
}
```
