<!-- このスニペットをプロジェクトの CLAUDE.md に統合する -->

## AI修正フロー（ai-dev-flow）

本プロジェクトには `.ai-flow/` の修正フローが導入されている。

- 修正タスクは `/ai-flow <タスク名>` で開始する（フロー統括は `.ai-flow/FLOW.md` が正）
- プロジェクト固有の値（技術スタック・コマンド・禁止事項・リスク分類）は `.ai-flow/project.yaml` が正。コード修正の前に必ず読む
- 単発の修正でも `.ai-flow/project.yaml` の `constraints`（禁止・必須・事故多発ポイント）と `git`（ブランチ・コミット規約）は遵守する
- ユーザー確認の前に `.ai-flow/knowledge/defaults.md`・`precedents.md` を引く（記載済み項目は確認不要）
- コミット/push の可否は `.ai-flow/project.yaml` の `git.commit_policy` に従う（`manual`: ユーザー明示指示時のみ／`auto`: フェーズ完了ごとに自動コミット・push、最終承認は PR マージ）
