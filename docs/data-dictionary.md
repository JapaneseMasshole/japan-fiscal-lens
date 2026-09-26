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
