# workflow-portfolio

このリポジトリは 2 つの独立した成果物が同居するモノレポ。

| パス | 内容 |
|------|------|
| `.ai-flow/` `adapters/` `docs/` | **ai-dev-flow** — AI支援修正フローの汎用配布パッケージ(素の Markdown + 設定ファイル。ここはパッケージの開発元であり導入先ではない) |
| `knowledge-hub/` | **Knowledge Hub** — ポートフォリオ用Webアプリ(社内ナレッジ/FAQ管理) |

## Knowledge Hub の構成

- `knowledge-hub/backend/` — Spring Boot 3 (Java 21) REST API。記事 CRUD + カテゴリ/タグ/キーワード検索
  - 永続化は `ArticleRepository` インターフェースで抽象化し、Spring プロファイルで切替:
    - `local`(デフォルト): インメモリ + シードデータ。AWS 不要
    - `prod`(Lambda): DynamoDB Enhanced Client。カテゴリ絞り込みは GSI `category-index`
  - Lambda 入口は `StreamLambdaHandler`(aws-serverless-java-container)。ローカル実行では使われない
- `knowledge-hub/frontend/` — Next.js 15 (App Router)。**SSR + Server Actions 構成であり SPA 化しない**(ユーザー方針)。クライアントコンポーネントは confirm ダイアログとフォームエラー表示など最小限に留める
- `knowledge-hub/infra/template.yaml` — SAM。Lambda + API Gateway HTTP API + DynamoDB を AWS 常時無料枠に収める構成(DynamoDB はプロビジョンド 5RCU/5WCU、無料枠維持のためオンデマンドに変えない)
- API のエラーレスポンスは `{"message": "...", "errors": ["field: 理由"]}` に統一(`ApiExceptionHandler`)

## ビルド・実行コマンド

この開発機の注意点:
- システム Java は 1.8。**JDK 21 は `C:\workspace\tools\jdk-21`**(ポータブル配置)。mvn 実行前に `$env:JAVA_HOME = "C:\workspace\tools\jdk-21"` を設定する
- **ポート 8080 は Oracle TNS Listener が占有**。バックエンドは `PORT=8081` で起動する(`frontend/.env.local` が 8081 を向いている。両ファイルとも git 管理外)

```powershell
# バックエンド: テスト / ローカル起動 (http://localhost:8081)
$env:JAVA_HOME = "C:\workspace\tools\jdk-21"; $env:PORT = "8081"
cd knowledge-hub/backend
mvn test
mvn spring-boot:run
```

```powershell
# フロントエンド: 開発サーバー (http://localhost:3000) / 検証
cd knowledge-hub/frontend
npm run dev
npm run typecheck; npm run build
```

## AI修正フロー（ai-dev-flow）

本プロジェクトには `.ai-flow/` の修正フローが導入されている。

- 修正タスクは `/ai-flow <タスク名>` で開始する（フロー統括は `.ai-flow/FLOW.md` が正）
- プロジェクト固有の値（技術スタック・コマンド・禁止事項・リスク分類）は `.ai-flow/project.yaml` が正。コード修正の前に必ず読む
- 単発の修正でも `.ai-flow/project.yaml` の `constraints`（禁止・必須・事故多発ポイント）と `git`（ブランチ・コミット規約）は遵守する
- ユーザー確認の前に `.ai-flow/knowledge/defaults.md`・`precedents.md` を引く（記載済み項目は確認不要）
- コミット/push の可否は `.ai-flow/project.yaml` の `git.commit_policy` に従う（`manual`: ユーザー明示指示時のみ／`auto`: フェーズ完了ごとに自動コミット・push、最終承認は PR マージ）

## 規約

- ドキュメント・コミットメッセージ・UI 文言は日本語
- CI (`.github/workflows/ci.yml`) は backend `mvn verify` / frontend `typecheck`+`build` / `sam validate` の 3 ジョブ。コミット前にローカルで相当のチェックを通すこと
- ai-dev-flow パッケージ側 (`.ai-flow/` 等) を変更するときは、それが配布物であることを意識する(プロジェクト固有の値を書き込まない。固有値の正は導入先の `project.yaml` という設計)
