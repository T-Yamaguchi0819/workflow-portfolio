# 前例集（判断履歴DB・チーム共有）

[2]Plan・[5]レビュー・[7]ドキュメントの調査では、**個別調査の前にまず本ファイルを引く**（推論ではなく検索で済ませ、調査の重複と判断ブレを防ぐ）。載っていない判断はユーザー確認・調査で確定させ、**確定した前例を追記**する。

> **`defaults.md` との役割分担**: defaults.md＝運用値・確認済み回答（「いつもこうする」）／本ファイル＝**判断の履歴**（「過去にこの状況でこう判断した。理由と再利用条件つき」）

## 設計判断の前例

<!-- 1判断=1エントリ。表形式で構造化し、後から検索・再利用できるようにする -->

| 項目 | 内容 |
|------|------|
| ID | P-001 |
| 確定日／タスク | {YYYY-MM-DD}／{タスクNo} |
| 対象 | {画面・機能・レイヤ} |
| 問題（何を判断する必要があったか） | {} |
| 判断 | {} |
| 理由 | {} |
| 採用案／不採用案 | 採用: {}／不採用: {}（理由） |
| 再利用条件（どんな時にこの前例を適用してよいか） | {} |

## ドキュメント記載慣行

<!-- 例: 「詳細設計は包括記載が慣行。個別項目の記載は基本設計側が担う」など、
     [7]で調査して確定した記載スタイルの前例 -->
- （追記していく）

## 実装パターンの前例

<!-- 例: 「○○機能の△△と同型の実装は□□方式」など、確定した参考実装の前例 -->
- （追記していく）

## 失敗事例（成功事例より価値がある。必ず記録する）

<!-- 1失敗=1エントリ。3回同種が並んだら guards/guard-rules.json・flow/・roles/ への
     ルール化（昇格）をユーザーに提案する（knowledge/README.md のサイクル） -->

| 項目 | 内容 |
|------|------|
| ID | F-001 |
| 発生日／タスク | 2026-08-14／knowledge-hub 初回AWSデプロイ |
| AIが誤った内容 | maven-shade の `<transformers>` を素で書き、spring-boot-starter-parent の shade pluginManagement 設定とマージされて設定解析エラー（Cannot find 'resource' in ServicesResourceTransformer） |
| 誤った理由・見落としたもの | 親POM側にも shade の設定があり、Maven が要素をインデックス対応でマージすることを見落とした |
| 人間がどう修正したか | エラー報告を受け、`<transformers combine.self="override">` で親設定を上書き |
| 今後の防止策 | Spring Boot 親POM配下で shade を使う場合は combine.self="override" を必ず付ける |
| ルール化ステータス | 未（同種3回でルール化検討） |

| 項目 | 内容 |
|------|------|
| ID | F-002 |
| 発生日／タスク | 2026-08-14／knowledge-hub 初回AWSデプロイ |
| AIが誤った内容 | spring-boot:repackage 後の jar（BOOT-INF 構造）を shade が包み、Lambda で Handler が ClassNotFoundException |
| 誤った理由・見落としたもの | 同一 package フェーズ内で repackage → shade の順に実行されることを考慮していなかった |
| 人間がどう修正したか | Lambda ログの ClassNotFound から特定。spring-boot-maven-plugin に `<classifier>boot</classifier>` を設定しメイン成果物をプレーン jar のまま維持 |
| 今後の防止策 | shade と spring-boot-maven-plugin を併用する場合は classifier 設定が必須 |
| ルール化ステータス | 未 |

| 項目 | 内容 |
|------|------|
| ID | F-003 |
| 発生日／タスク | 2026-08-14／knowledge-hub 初回AWSデプロイ |
| AIが誤った内容 | spring.factories を AppendingTransformer で単純結合。同一キーが後勝ちになり EnvironmentPostProcessorApplicationListener が消えて application.yml が読み込まれず、SnapStart 初期化で起動失敗 |
| 誤った理由・見落としたもの | Properties は重複キーが後勝ちであること。spring-boot と spring-boot-autoconfigure が同じキーを持つこと |
| 人間がどう修正したか | 「placeholder 未解決」ログ→結合後の spring.factories を実際に dump して重複キーを確認。Spring Boot 提供の PropertiesMergingResourceTransformer に置換 |
| 今後の防止策 | Spring Boot を shade する場合、spring.factories は必ず PropertiesMergingResourceTransformer でマージする |
| ルール化ステータス | 未 |

| 項目 | 内容 |
|------|------|
| ID | F-004 |
| 発生日／タスク | 2026-08-14／knowledge-hub 初回AWSデプロイ |
| AIが誤った内容 | API Gateway **HTTP API**（ペイロード v2.0）に対し REST API（v1.0）用の getAwsProxyHandler を実装し、InvalidRequestEventException で全リクエスト 500 |
| 誤った理由・見落としたもの | HTTP API のデフォルトペイロード形式が v2.0 であること |
| 人間がどう修正したか | Lambda ログから特定し getHttpApiV2ProxyHandler + HttpApiV2ProxyRequest に変更 |
| 今後の防止策 | aws-serverless-java-container 使用時は API Gateway の種類（REST/HTTP）とハンドラの対応を必ず確認 |
| ルール化ステータス | 未 |

| 項目 | 内容 |
|------|------|
| ID | F-005 |
| 発生日／タスク | 2026-08-14／knowledge-hub 初回AWSデプロイ |
| AIが誤った内容 | SAM の template.yaml に日本語コメントを記載。Windows の SAM CLI がロケールエンコーディング（cp932）で読み UnicodeDecodeError |
| 誤った理由・見落としたもの | SAM CLI (Windows) がテンプレートを UTF-8 でなくシステムロケールで読むこと |
| 人間がどう修正したか | ユーザーのデプロイ失敗報告を受け、template.yaml を ASCII（英語コメント）のみに書き換え。ファイル冒頭に ASCII-only の注記を追加 |
| 今後の防止策 | SAM/CloudFormation テンプレートと samconfig.toml は ASCII のみで書く（このリポジトリの慣行として固定。samconfig.toml でも再発を確認済み） |
| ルール化ステータス | 未 |

| 項目 | 内容 |
|------|------|
| ID | F-006 |
| 発生日／タスク | 2026-08-14／GitHub Actions CD 構築 |
| AIが誤った内容 | deploy ジョブに `environment: production` を指定し、OIDC トークンの sub が `environment:production` 形式に変わって IAM 信頼条件（`ref:refs/heads/main`）と不一致 → AssumeRole 拒否で CD 失敗 |
| 誤った理由・見落としたもの | GitHub Environment 指定が OIDC の sub クレーム形式を変えるという仕様 |
| 人間がどう修正したか | Actions の失敗ログ（Not authorized to perform sts:AssumeRoleWithWebIdentity）から特定し、environment 指定を削除 |
| 今後の防止策 | OIDC の信頼条件と workflow の environment 指定は必ずセットで設計する（片方だけ変えない）。deploy.yml にコメントで注意書き済み |
| ルール化ステータス | 未 |

| 項目 | 内容 |
|------|------|
| ID | F-007 |
| 発生日／タスク | 2026-08-14／GitHub Actions CD 構築 |
| AIが誤った内容 | OIDC 信頼条件の sub を旧形式（repo:owner/repo:ref:...）で記述。GitHub の仕様変更で sub は owner@ownerId/repo@repoId の ID 埋め込み形式になっており不一致 → AssumeRole 拒否 |
| 誤った理由・見落としたもの | GitHub OIDC の sub クレーム形式変更（改名なりすまし対策で不変 ID が埋め込まれる）。学習時点の知識で書き、実際のクレームを確認しなかった |
| 人間がどう修正したか | CloudTrail の AccessDenied イベントから実際の sub を取得して特定。信頼条件を ID 埋め込み形式に修正（gh api で ID を照合） |
| 今後の防止策 | OIDC 連携の失敗調査は推測でなく CloudTrail の実クレームを見る。sub 形式は変わり得る前提で、拒否時はまず実物と突き合わせる |
| ルール化ステータス | 未 |
