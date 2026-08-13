# docs-style — ドキュメント書式のテンプレート置き場

正式ドキュメント（設計書・テスト仕様書・運用手順書等）の書式を、**ハイブリッド方式**で管理する:

| 役割 | ファイル | 用途 |
|------|---------|------|
| **検証用スペック** | `{ドキュメント名}.style.yaml` | [7]で更新後の Excel を機械検査する「書式の正」（許可フォント・表のヘッダ構成等） |
| **生成用の雛形** | `雛形_{用途}.xlsx` | 新規の節・シートは YAML から書式を再構築せず、**雛形のコピー**で作る（図形・グラフは YAML で表現できないため） |
| **索引** | style YAML の `templates` 節・`project.yaml` の `docs.targets` | どの対象にどの style / 雛形を使うかの対応 |

## 作り方（導入時。詳細は docs/導入ガイド.md）

1. 対象ドキュメントの代表サンプルを1件ずつ用意する（設計書だけでなくテスト仕様書等も）
2. `python .ai-flow/guards/extract_excel_style.py <サンプル.xlsx>` で下書きを生成する
3. **人間がレビューして確定する**（styles の命名・`validation.allowed_fonts` の絞り込み・`patterns` の追記）。確定した YAML を本ディレクトリへ置き、`project.yaml` の `docs.targets[].style` にパスを記入する
4. 新規作成が発生し得る単位（機能節・テストケース表等）を雛形 .xlsx として切り出し、本ディレクトリへ置く

## 検査（[7]ドキュメント反映で実行）

```
python .ai-flow/guards/verify_excel_style.py --style .ai-flow/docs-style/{名前}.style.yaml <更新したファイル>
```

ERROR は解消してからゲートへ進む。誤検知と考える場合も独断で style YAML を書き換えず、ユーザーに確認する（確定済み YAML の変更は人間の承認事項）。

## 注意

- **openpyxl での Excel 保存は原則禁止**（図形・グラフを破壊し得る）。書き込みは `project.yaml` の `docs.excel_write_policy` に従う（Windows なら Excel COM 経由を推奨）。読み取り（抽出・検査）は安全
- patterns の位置決めは**セル座標でなくラベル（anchor）**で行う。人間の行挿入で座標ベースの定義は腐るため
