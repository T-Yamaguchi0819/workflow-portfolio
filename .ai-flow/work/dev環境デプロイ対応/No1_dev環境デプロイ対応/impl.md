<!-- 本ファイルは [5]独立レビューには渡さない（実装者の解釈を引き継がないため）。[8]ナレッジ化・人間監査用 -->
# 実装記録 No1: dev環境デプロイ対応

## 実施日・実施範囲

- 実施日: 2026-08-14
- ブランチ: `ai/dev-env-deploy`（実装時に `git branch --show-current` で確認済み）
- 範囲: plan.md ②の 1〜5（ファイル変更のみ）。**AWS 側操作（実施順序 2〜5: prod チェンジセット確認・OIDC スタック更新・push・Amplify 設定）は本フェーズでは未実施**（統括が後続で扱う）。コミットも未実施（commit_policy=manual）

## 変更ファイルと変更内容

### 1. `knowledge-hub/infra/template.yaml`

物理リソース名 3 点のみを `${AWS::StackName}` ベースへ変更（plan ③-1 どおり）:

- `ArticlesTable.TableName`: `knowledge-hub-articles` → `!Sub '${AWS::StackName}-articles'`（変更理由の ASCII コメントを直上に追加）
- `ApiFunction.FunctionName`: `knowledge-hub-api` → `!Sub '${AWS::StackName}-api'`
- `HttpApi.Name`: `knowledge-hub-http-api` → `!Sub '${AWS::StackName}-http-api'`
- キャパシティ（5/5+5/5）・BillingMode: PROVISIONED・SnapStart・MemorySize 512・CORS パラメータ定義は不変

### 2. `knowledge-hub/infra/samconfig.toml`

末尾に `[dev.deploy.parameters]`（stack_name=knowledge-hub-dev、s3_prefix=knowledge-hub-dev、confirm_changeset=false）を追加。`parameter_overrides` なし（CorsAllowedOrigin はテンプレートデフォルト維持）・`profile` なし（CI は OIDC）。`[default.*]` は無変更。

### 3. `.github/workflows/deploy.yml`

- トリガー: `branches: [main]` → `[main, 'ai/**']`（paths 不変）
- `Resolve target environment` ステップ（id: env）を steps 先頭に追加。case 分岐で main→`default`/`knowledge-hub`、`ai/*`→`dev`/`knowledge-hub-dev`、それ以外→`exit 1`（フェイルクローズ）
- `sam deploy` に `--config-env ${{ steps.env.outputs.config_env }}` を追加
- スモークテストの `describe-stacks --stack-name` を `${{ steps.env.outputs.stack_name }}` に変更
- concurrency group を `deploy-knowledge-hub-${{ github.ref == 'refs/heads/main' && 'prod' || 'dev' }}` に分離（cancel-in-progress: false 維持）
- `environment:` 指定は追加していない（F-006）。冒頭コメントと concurrency コメントを更新（plan ⑤「変更可能」の範囲）

### 4. `knowledge-hub/infra/github-oidc.yaml`

`DeployRole` 信頼条件の sub を `StringEquals` 単一値 → `StringLike` リスト（main + `ai/*`。両方とも ID 埋め込み形式 `${GitHubOrg}@${GitHubOrgId}/${RepositoryName}@${RepositoryId}` を維持=F-007）へ変更。aud の StringEquals・ロール名・MaxSessionDuration・ManagedPolicyArns は不変。sub に付随していたコメントブロックは StringLike 直上へ移設し内容を現状に合わせて更新（ASCII のみ）。

### 5. `.ai-flow/project.yaml`

`verify` セクションのみ変更:

- `method`: plan ③-5 の文言どおり dev 環境確認に更新
- `local_env` のコメント行に dev API の取得元（スタック Output `ApiEndpoint`）を追記。他キーは不変

## 自己チェック結果

| 検査 | 結果 |
|------|------|
| ASCII-only（template.yaml / samconfig.toml / github-oidc.yaml。F-005） | 3 ファイルとも非 ASCII 文字なし（`grep -P '[^\x00-\x7F]'` で確認） |
| sam validate --lint | **SAM CLI がこの開発機に未導入のため実行不可**。代替として lint 実体の cfn-lint 1.55.1（pip 導入）で `template.yaml`・`github-oidc.yaml` を検査 → **両方とも指摘 0 件（exit 0）** |
| deploy.yml 構文 | YAML パース OK（PyYAML）。branches / concurrency.group / steps 構成が plan どおりであることを機械抽出で確認 |
| deploy.yml 内シェル | 全 run スクリプト `bash -n` OK。環境解決 case を実行シミュレーション: `main`→default/knowledge-hub、`ai/dev-env-deploy`→dev/knowledge-hub-dev、`ai/fix/foo`→dev（多階層一致）、`feature/x`→**exit 1（フェイルクローズ動作確認）** |
| samconfig.toml 構文 | TOML パース OK（tomllib）。dev セクションに parameter_overrides が無いこと・default セクション不変を確認 |
| guards | `python .ai-flow/guards/verify_diff.py --repo .` → **ERROR 0 件 / WARN 0 件** |
| compile_command（mvn / npm） | 未実行。アプリコード（backend/frontend）に差分なしのため統括指示により YAML 妥当性確認で代替（CI の mvn verify は push 時に従来どおり実行される） |
| [3] テスト | スキップ（2026-08-14 ユーザー承認済み。チェンジセット確認＋デプロイ内蔵スモーク＋[6]で代替） |
| 変更禁止リスト（plan ⑤） | 侵害なし: prod 物理名は prod スタックで従来値に解決・キャパシティ/課金モード不変・main トリガー/デプロイ手順不変・OIDC ロール名/main 信頼/ID 埋め込み形式維持・environment: 追加なし・amplify.yml/アプリコード無変更・秘密情報なし |
| スコープ外変更 | なし（git diff は上記 5 ファイルのみ。`.ai-flow/knowledge/defaults.md` の差分は前フェーズ由来で本フェーズでは触れていない） |

## 迷った判断（記録）

1. **template.yaml の TableName 直上に説明コメントを追加**: plan ③-1 は「他は一切変更しない」だが、`!Sub` 化の理由（prod で従来物理名に一致させ置換を防ぐ制約）はコードから読めない Why-not と判断し、変更行に付随する ASCII コメントとして追加した（変更対象そのものの一部という解釈）。
2. **github-oidc.yaml の stale な Description を未修正**: テンプレート冒頭 Description と `DeployRole.Description` に「main branch only」の記述が残り、今回の拡張後は実態と不一致になる。しかし plan ③-4 が「その他プロパティは変更しない」と明記しており（Description 変更は IAM ロールの Modify 更新を伴う）、Critical 案件のためスコープ厳守を優先して据え置いた。末尾の「limited to one repo/branch」コメントも同様。→ [5]レビュー/[7]ドキュメントでの扱いを統括へ申し送り（機能影響なし・未解決事項とはしない）。
3. **Resolve target environment ステップの位置**: plan は位置を指定していない。リポジトリファイルを参照しないため checkout より前（steps 先頭）に置き、想定外 ref を最速で失敗させる構成にした。
4. **verify.local_env への dev 補足**: plan の「必要に応じ追記」を、値の書き換えではなくコメント行への追記（dev API はスタック Output `ApiEndpoint`）で満たした。ローカル起動手順自体は補助として残るため参照先の値は不変とした。

## [5]レビュー推奨指摘への対応（2026-08-14 追記）

[5]独立レビューは PASS（要修正なし）。推奨指摘 2 件に統括指示の方針で対応した:

1. **推奨1（github-oidc.yaml の「main only」記述乖離）**: テンプレート冒頭 Description と末尾の行コメントを main + ai/* の実態に合わせて修正（ASCII 維持）。`DeployRole.Description` プロパティは統括判断で据え置き（plan ③-4「その他プロパティは変更しない」優先。上記「迷った判断 2」の申し送りが指摘#1 と同件で、プロパティ据え置きの線で確定）
2. **推奨2（deploy.yml NOTE コメントの信頼条件記述）**: 「(ref:refs/heads/main と ref:refs/heads/ai/*)」に修正

再検査: github-oidc.yaml ASCII OK・cfn-lint 指摘 0 件／deploy.yml YAML パース OK／guards ERROR 0 件。対応内容は review.md「対応記録」欄にも記録済み。

## 残作業（本フェーズ外・統括対応）

- plan「実施順序」2〜5: prod チェンジセット事前確認（`sam deploy --no-execute-changeset --profile portfolio`。**要 SAM CLI**＝この開発機に未導入の点に注意）→ OIDC スタック `knowledge-hub-github-oidc` 更新 → push（ユーザー指示後）→ Amplify update-app / create-branch
- コミット（commit_policy=manual。ユーザー指示待ち）
