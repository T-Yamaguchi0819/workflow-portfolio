# [0] 初期化（ブランチ作成・作業ディレクトリ初期化）

## 前提（最初に読む）

1. `.ai-flow/project.yaml`（`git.branch_prefix`・`flow.work_dir`・対象リポジトリ）
2. `.ai-flow/knowledge/defaults.md`・`defaults.local.md`（存在すれば）

## 手順

1. **タスク名の確定**: ユーザーの指示からタスク名を決める（例: `不具合_一覧画面表示崩れ`・`フェーズ2.1`）。作業ディレクトリ名・ブランチ名に使う
2. **ブランチ作成**: 対象リポジトリごとに、現在のブランチ・未コミット変更を確認したうえで、`{branch_prefix}{タスク内容がわかる名前}` のブランチを作成する（例: `ai/announce-list-fix`）。未コミット変更が既にある場合は**勝手に stash せず**未解決事項として報告する
3. **作業ディレクトリ作成**: `{work_dir}/{タスク名}/` を作成し、`templates/_state.md` をコピーして `_state.md` を作る。判明している基本情報（タスク名・ブランチ・モード・入力元）を記入する
4. **defaults.local.md の確認**: `.ai-flow/knowledge/defaults.local.md` が無い場合、`defaults.local.example.md` を元に必要項目（担当者名・マシン固有の環境情報）をユーザーに質問して生成する（未回答なら未解決事項として返す）
5. **ドキュメント書式テンプレートの確認**（`docs.enabled: true` の場合のみ）: `docs.targets` の**全対象**（設計書だけでなくテスト仕様書等も）について `sample`・`style` の設定を確認する。未記入の対象があれば、代表サンプルドキュメントの有無・所在をユーザーに一括で質問する（未回答なら未解決事項として返す）。回答は `knowledge/defaults.md` へ記録し、**次タスク以降は再確認しない**（「サンプルなし・書式管理不要」の回答もその旨を記録して以後スキップ）。サンプルが得られたら `guards/extract_excel_style.py` で style YAML の下書きを生成し、確定（レビュー）をユーザーに依頼する（手順は `docs-style/README.md`）
6. **Issue 作成**（`project.yaml` の `issue_sync.enabled: true` の場合のみ）: `gh issue create` でタスク用 Issue を1件作成し（タイトル=タスク名、`issue_sync.labels` を付与、`issue_sync.repo` 指定があればそのリポジトリへ）、Issue 番号を `_state.md` の基本情報に記録する。`gh` が使えない場合は作成をスキップし、Issue 欄に「なし（gh 利用不可）」と記録して続行する（以降の運用は FLOW.md の「GitHub Issue ミラー」節が正）

## 成果物

- 新ブランチ（対象リポジトリ分）
- `{work_dir}/{タスク名}/_state.md`
- タスク用 Issue（`issue_sync` 有効時のみ）

## 完了条件

- `_state.md` の基本情報が埋まり、進捗マトリクスの [0] が ✓ になっている
