# Data license and attribution / データの利用条件と出典

The code in this repository is MIT-licensed. **The data is not ours.** It belongs to the government bodies that publish it, and its reuse follows their terms.

本リポジトリのコードは MIT ライセンスですが、**データの権利は各公表機関に帰属します。** 利用条件は各機関の定めに従います。

## Publishers / 公表機関

| Publisher | Terms |
|---|---|
| 財務省 Ministry of Finance | Website terms of use (利用規約). Compatible with CC BY 4.0 under the Government Standard Terms of Use (政府標準利用規約 第2.0版). |
| 総務省 Ministry of Internal Affairs and Communications | Website terms of use. Compatible with CC BY 4.0 under the Government Standard Terms of Use (政府標準利用規約 第2.0版). |
| 日本銀行 Bank of Japan | Statistics may be reused with source attribution, per the BOJ website terms. |

Each ministry's current terms are linked from the footer of its website. Check them before reusing data from this repository in your own work.

## How attribution works here / 出典表示の方法

- Every dataset has an entry in [`data/sources.yaml`](data/sources.yaml) with its publisher and source URL.
- Every chart on the site shows its source and links to the original file.
- Processed data (`data/processed/`, `web/public/data/`) is **edited** (reshaped, units unified). Per the Government Standard Terms, the site says so and does not present processed figures as if they were the government's own tables.

加工したデータ（`data/processed/`、`web/public/data/`）は、形式の変換や単位の統一などの**編集・加工**を行っています。政府標準利用規約に従い、加工を行った旨を明示し、国が作成したものであるかのような表示はしません。
