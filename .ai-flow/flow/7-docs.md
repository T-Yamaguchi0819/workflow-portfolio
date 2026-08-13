# [7] 正式ドキュメント反映

**目的**: 実装変更を正式ドキュメント（設計書等）へ反映する。`project.yaml` の `docs.enabled: false` のプロジェクト、または [2]Plan で「反映不要」承認済みの場合は本フェーズをスキップする（進捗マトリクスに ➖）。

## 前提（最初に読む）

1. `_state.md`・対象 No の `要件.md`・`plan.md`（ドキュメント反映方針・前例調査結果）・`impl.md`（実際の変更内容）
2. `.ai-flow/project.yaml`（`docs.targets`・`docs.policy`・`docs.excel_write_policy`）
3. `.ai-flow/knowledge/precedents.md`（記載慣行。**個別調査より先に引く**）
4. 対象の style YAML・雛形（`docs.targets[].style`・`templates`。設定されている場合。役割分担は `docs-style/README.md`）

## 手順

1. `docs.policy` に専用の更新手順・禁止事項（例: 特定ツールでの保存禁止・検証手順）が定義されている場合、**必ずその手順に従う**
2. **実装コードを参照して正確に記載する**（推測で書かない）。反映内容は plan.md の方針と impl.md の実変更に基づく
3. 記載スタイルは既存ドキュメントの慣行に合わせる（precedents.md の記載慣行 → 類似機能の記載例の順で確認）。**対象が Excel の場合**: 新規の節・シートは雛形 .xlsx（`docs.targets[].templates`）のコピーから作成し、書き込みは `docs.excel_write_policy` に従う（openpyxl での直接保存は図形・グラフを破壊し得るため原則禁止）
4. ドキュメント内の相互参照（目次・項番・図表と本文の対応）が変更後も一致していることを確認する
5. **書式検査**（`style` 設定時）: `python .ai-flow/guards/verify_excel_style.py --style {style} {更新したファイル}` を実行し、ERROR を解消してからゲートへ進む（誤検知と考える場合も独断で style YAML を書き換えず、ユーザーに確認する）
6. `No{N}_{機能名}/docs.md` に、更新したドキュメント・箇所・検証結果（書式検査の結果を含む）を記録する
7. 新たに確定した記載慣行は precedents.md へ追記する（機械検査可能な書式ルールは style YAML への追記を**ユーザーに提案**する）

## 成果物

- 更新済み正式ドキュメント・`No{N}_{機能名}/docs.md`

## ゲート（必須）

ドキュメントの変更内容（検証手順があればその結果も）をユーザーに提示し、確認を得る。
