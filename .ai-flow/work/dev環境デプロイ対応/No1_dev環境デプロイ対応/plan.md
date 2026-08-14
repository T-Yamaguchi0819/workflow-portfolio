# 修正Plan No1: dev環境デプロイ対応

## ① 要件（要約）

開発段階ブランチ（`ai/*`）を AWS の**共有 dev 環境**へデプロイ可能にし、[6]動作確認をデプロイ済み dev 環境で行えるようにする。

- バックエンド: SAM スタック `knowledge-hub-dev` を新設。`ai/**` push で GitHub Actions が自動デプロイし、スモークテスト（`GET /api/articles` = 200）まで実施
- フロントエンド: Amplify（appId=d1e1o87p5asykz）の自動ブランチ作成（`ai/*`）でブランチ毎にデプロイ。branch 用 `API_BASE_URL` は dev API を向け、ブランチ削除で環境も自動削除
- **絶対条件**: prod（スタック `knowledge-hub`）のリソース置換・再作成・削除が一切発生しないこと。main push の prod デプロイは挙動・リソースとも不変
- dev の `CorsAllowedOrigin` はデフォルト値のまま（SSR 経由のみでブラウザ直呼びなし）。DynamoDB 合計 20RCU/20WCU で無料枠 25 以内

## ② 対象ファイル一覧

| # | ファイル（フルパス） | 区分 |
|---|---------------------|------|
| 1 | `C:\workspace\workflow-portfolio\knowledge-hub\infra\template.yaml` | インフラ定義（SAM） |
| 2 | `C:\workspace\workflow-portfolio\knowledge-hub\infra\samconfig.toml` | 設定（SAM デプロイ環境） |
| 3 | `C:\workspace\workflow-portfolio\.github\workflows\deploy.yml` | CI/CD（GitHub Actions） |
| 4 | `C:\workspace\workflow-portfolio\knowledge-hub\infra\github-oidc.yaml` | インフラ定義（IAM OIDC 信頼条件） |
| 5 | `C:\workspace\workflow-portfolio\.ai-flow\project.yaml` | フロー設定（verify.method） |
| 6 | （git 管理外）Amplify アプリ設定 appId=d1e1o87p5asykz | AWS 側設定（CLI 実施＋手順をドキュメント化） |
| 7 | `C:\workspace\workflow-portfolio\knowledge-hub\README.md` ほか docs（⑧参照） | ドキュメント（[7]で反映） |

※ アプリコード（backend / frontend）・`amplify.yml` は**変更しない**。

## ③ 変更方針（ファイルごとに具体的に）

### 1. knowledge-hub/infra/template.yaml

物理リソース名 3 点を `${AWS::StackName}` ベースに変更する（他は一切変更しない。ASCII のみ維持＝F-005）:

| リソース | 現行（固定） | 変更後 | prod（スタック名 `knowledge-hub`）での解決結果 |
|---------|-------------|--------|---------------------------------------------|
| ArticlesTable.TableName | `knowledge-hub-articles` | `!Sub '${AWS::StackName}-articles'` | `knowledge-hub-articles`（現行と同一） |
| ApiFunction.FunctionName | `knowledge-hub-api` | `!Sub '${AWS::StackName}-api'` | `knowledge-hub-api`（同一） |
| HttpApi.Name | `knowledge-hub-http-api` | `!Sub '${AWS::StackName}-http-api'` | `knowledge-hub-http-api`（同一） |

- CloudFormation は `Fn::Sub` を解決した後の値でプロパティ差分を判定するため、prod では**差分なし（空チェンジセット）**となる想定。実装後に `sam deploy --no-execute-changeset --profile portfolio`（default 環境）でチェンジセットを事前作成し、「変更なし」または Modify のみであることを確認してから main へ入れる（AC の絶対条件の検証方法）
- dev スタック（`knowledge-hub-dev`）では `knowledge-hub-dev-articles` / `knowledge-hub-dev-api` / `knowledge-hub-dev-http-api` に解決され、prod と衝突しない
- キャパシティ（テーブル 5/5 + GSI 5/5）・BillingMode・SnapStart・MemorySize 512・CORS パラメータ定義は**変更しない**

### 2. knowledge-hub/infra/samconfig.toml

`[dev.deploy.parameters]` を追加（ASCII のみ維持）:

```toml
[dev.deploy.parameters]
stack_name = "knowledge-hub-dev"
resolve_s3 = true
s3_prefix = "knowledge-hub-dev"
region = "ap-northeast-1"
confirm_changeset = false
capabilities = "CAPABILITY_IAM"
image_repositories = []
```

- `parameter_overrides` は**書かない** → `CorsAllowedOrigin` はテンプレートデフォルト `http://localhost:3000` のまま（AC で確定済み）
- `profile` は書かない（CI は OIDC 認証。既存方針を踏襲）
- `[default.*]`（prod）のセクションは一切変更しない

### 3. .github/workflows/deploy.yml

3 点を変更する:

**(a) トリガー**: `branches: [main]` → `branches: [main, 'ai/**']`（paths 条件は現行のまま変更しない）

**(b) 環境振り分け**（フェイルクローズ設計。誤って prod へ向かうことを構造的に排除）:

```yaml
- name: Resolve target environment
  id: env
  run: |
    case "${GITHUB_REF}" in
      refs/heads/main)
        echo "config_env=default" >> "$GITHUB_OUTPUT"
        echo "stack_name=knowledge-hub" >> "$GITHUB_OUTPUT" ;;
      refs/heads/ai/*)
        echo "config_env=dev" >> "$GITHUB_OUTPUT"
        echo "stack_name=knowledge-hub-dev" >> "$GITHUB_OUTPUT" ;;
      *)
        echo "Unexpected ref: ${GITHUB_REF}" >&2
        exit 1 ;;
    esac
```

- `sam deploy` を `--config-env ${{ steps.env.outputs.config_env }} --no-confirm-changeset --no-fail-on-empty-changeset` に変更
- スモークテストの `describe-stacks --stack-name` を `${{ steps.env.outputs.stack_name }}` に変更（dev は dev の ApiEndpoint を叩く）
- 副次修正: 現行では `workflow_dispatch` を任意ブランチから実行すると prod へデプロイされ得るが、上記 case 分岐により main/ai/** 以外は**ジョブ失敗（デプロイなし）**となり安全側に倒れる
- `environment:` 指定は追加しない（F-006）

**(c) concurrency**: prod/dev を別グループに分離し、相互キャンセル・直列待ちを排除:

```yaml
concurrency:
  group: deploy-knowledge-hub-${{ github.ref == 'refs/heads/main' && 'prod' || 'dev' }}
  cancel-in-progress: false
```

- prod グループと dev グループが独立 → main のデプロイと ai/** のデプロイは並行実行可能
- dev グループ内は直列。GitHub の仕様で待機枠は 1 つ（複数 ai ブランチからの同時 push は最新の待機だけが残り古い待機はキャンセル）＝AC の「後勝ち」許容と整合
- `cancel-in-progress: false` 維持（実行中デプロイは中断しない）

### 4. knowledge-hub/infra/github-oidc.yaml

信頼条件の sub を `StringEquals` 単一値 → `StringLike` リスト（main + `ai/*`）へ拡張（ID 埋め込み形式は維持＝F-007。ASCII のみ維持）:

```yaml
Condition:
  StringEquals:
    token.actions.githubusercontent.com:aud: sts.amazonaws.com
  StringLike:
    token.actions.githubusercontent.com:sub:
      - !Sub repo:${GitHubOrg}@${GitHubOrgId}/${RepositoryName}@${RepositoryId}:ref:refs/heads/main
      - !Sub repo:${GitHubOrg}@${GitHubOrgId}/${RepositoryName}@${RepositoryId}:ref:refs/heads/ai/*
```

- `StringLike` でワイルドカードなしの値は完全一致として評価されるため、main の信頼は**実質不変**（縮小しない）
- ロール名 `knowledge-hub-github-deploy`・aud 条件・その他プロパティは変更しない
- 反映は CloudFormation スタック **`knowledge-hub-github-oidc`**（AWS 照会で実在確認済み）の更新:
  `aws cloudformation deploy --stack-name knowledge-hub-github-oidc --template-file github-oidc.yaml --capabilities CAPABILITY_NAMED_IAM --profile portfolio --region ap-northeast-1`
  （IAM Role の**信頼ポリシー変更のみ＝置換なし**。RoleName 不変のため Modify 更新）

### 5. .ai-flow/project.yaml

`verify.method` を更新（`verify` セクションのみ変更。他キーは触れない）:

> dev 環境で確認: `ai/**` へ push すると GitHub Actions が SAM スタック `knowledge-hub-dev` をデプロイし、Amplify が当該ブランチのフロントエンドを自動デプロイする。デプロイ済みのブランチ URL で CRUD と検索の通しを最低限確認する（ローカル起動での事前確認は任意の補助）

必要に応じ `verify.local_env` に dev 環境の補足（dev API はスタック Output `ApiEndpoint`）を追記。

### 6. Amplify 設定（git 管理外・AWS 側。設定手段＝AWS CLI で確定）

現況（read-only 照会で確認済み）: `enableAutoBranchCreation=false`、`enableBranchAutoDeletion=false`、`API_BASE_URL` は**アプリレベル**環境変数で prod URL（`https://nx7936lj07...`）、main ブランチにブランチ個別 env なし。

設定コマンド（dev API エンドポイント判明後に実施。`<DEV_API>` を置換）:

```
aws amplify update-app --app-id d1e1o87p5asykz --profile portfolio --region ap-northeast-1 ^
  --enable-auto-branch-creation ^
  --enable-branch-auto-deletion ^
  --auto-branch-creation-patterns "ai/*" "ai/**" ^
  --auto-branch-creation-config "{\"stage\":\"DEVELOPMENT\",\"framework\":\"Next.js - SSR\",\"enableAutoBuild\":true,\"enablePullRequestPreview\":false,\"environmentVariables\":{\"API_BASE_URL\":\"<DEV_API>\"}}"
```

- `autoBranchCreationConfig.environmentVariables` の `API_BASE_URL` は**ブランチレベル**で設定され、アプリレベル（prod URL）を上書きする。main はブランチ env を持たないためアプリレベル（prod）のまま＝AC「main の API_BASE_URL は prod のまま」を満たす
- アプリレベル環境変数・main ブランチ設定・`amplify.yml` は変更しない（既存の `env | grep API_BASE_URL >> .env.production` がブランチ env でもそのまま機能する）
- **実施タイミングの順序依存**（下記「実施順序」参照）: dev API エンドポイントは dev スタック初回デプロイ後にしか判明しないため、OIDC 更新 → ai ブランチ push（dev スタック作成）→ 本コマンド、の順
- **注意（初回ブランチの取り込み）**: 自動ブランチ作成は「設定後に push で新規作成されたブランチ」に対して発火する。本タスクのブランチ `ai/dev-env-deploy` は設定時点で push 済みの可能性が高く、その場合は手動で 1 回だけ作成する:
  `aws amplify create-branch --app-id d1e1o87p5asykz --branch-name ai/dev-env-deploy --stage DEVELOPMENT --framework "Next.js - SSR" --enable-auto-build --environment-variables API_BASE_URL=<DEV_API> --profile portfolio --region ap-northeast-1`
- 設定手順は [7] でドキュメントに記録する（記載先候補: `knowledge-hub/README.md` のデプロイ節。⑧参照）

### 実施順序（順序依存の確定）

| 順 | 作業 | 実施者/場所 |
|----|------|------------|
| 1 | [3][4] ファイル変更（②の 1〜5）を `ai/dev-env-deploy` 上で実施 | AI（ローカル） |
| 2 | prod 無置換の事前検証: `sam deploy --no-execute-changeset --profile portfolio`（default 環境）でチェンジセット確認 → 実行せず削除 | AI（ローカル・要ユーザー同意） |
| 3 | OIDC スタック `knowledge-hub-github-oidc` を更新（③-4 のコマンド）。**ai/** push より先に行う**（先に push すると AssumeRole 拒否で workflow 失敗するため） | 要確認（ユーザー実施 or AI 実施の承認） |
| 4 | `ai/dev-env-deploy` を push（commit_policy=manual のためユーザー指示後）→ Actions が `knowledge-hub-dev` を初回デプロイ → Output `ApiEndpoint` を取得 | ユーザー指示後 |
| 5 | Amplify update-app（＋既存ブランチ分の create-branch）を実施 | 同上（順 3 と同じ確認） |
| 6 | [6] 動作確認: Amplify ブランチ URL で CRUD・検索の通し／main 側の不変確認 | AI＋ユーザー |

### 多階層ブランチ（`ai/a/b`）の一致範囲確認結果（AC から本フェーズへ委譲された調査）

| 経路 | パターン | `ai/foo`（1階層） | `ai/fix/foo`（多階層） | 根拠 |
|------|---------|------------------|----------------------|------|
| GitHub Actions `branches` | `ai/**` | 一致 | 一致 | Actions のブランチフィルタは `*` が `/` を跨がず `**` が跨ぐ仕様のため `ai/**` を採用 |
| IAM 信頼条件 | `StringLike` `.../ai/*` | 一致 | **一致** | IAM ポリシーの `*` はパス非依存で `/` を含む任意文字列に一致 |
| Amplify 自動ブランチ作成 | `ai/*` と `ai/**` の両方を登録 | 一致 | `ai/**` で一致する想定 | Amplify のパターンは `*` が 1 階層、`**` が階層跨ぎ。両方登録して確実化。多階層の実挙動は設定時（順 5 以降）に検証し結果をドキュメントへ記録 |

→ AC の最低条件「`ai/{1階層}` が全経路で動作」は 3 経路とも確実に満たす。多階層もバックエンド経路（Actions＋IAM）は確実、Amplify のみ設定時検証とする。

## ④ 影響範囲（依存レイヤの連鎖を明示する)

- 依存レイヤ連鎖: GitHub push → Actions（deploy.yml）→ OIDC AssumeRole（IAM 信頼条件）→ SAM/CloudFormation（template.yaml + samconfig.toml）→ Lambda/API Gateway/DynamoDB（物理リソース）。フロント側は GitHub push → Amplify（アプリ設定 + amplify.yml）→ ブランチ環境（SSR ランタイム env `API_BASE_URL`）→ dev API。**アプリケーションコード層（Controller/Service/Repository）には一切届かない**
- 呼び出し元: prod フロント（`https://main.d1e1o87p5asykz.amplifyapp.com` の SSR）→ prod API。物理名・URL 不変のため影響なし
- 関連画面・機能: 全画面（S-01〜S-04）が dev 環境でも動く必要がある（動作確認の対象。コード変更はなし）
- DB: dev スタックで新テーブル `knowledge-hub-dev-articles`（+GSI）が**新規作成**される。prod テーブルは名前・定義・データとも不変。キャパシティ合計 prod 10RCU/10WCU + dev 10RCU/10WCU = 20/20 ≤ 無料枠 25。**dev テーブルは初期データ空**（prod プロファイルにシードなし）→ [6] で UI から記事を作成して確認する
- 権限・ロールによる差異: アプリに認証機能なし。IAM は `knowledge-hub-github-deploy` ロールの信頼範囲が main + `ai/*` に**拡張**される（AdministratorAccess 付与ロールのため信頼条件が唯一のガード。Critical 判定の主因）
- Lambda: dev 用に 512MB 関数がもう 1 本増える（アカウント上限 512MB/関数は変わらず。無料枠はリクエスト/実行時間ベースで dev の利用量は僅少）

## ⑤ 変更分類（レビュー[5]の必須確認項目）

| 分類 | 対象 |
|------|------|
| 変更対象（今回修正するもの） | template.yaml の物理名 3 点（`!Sub` 化のみ）／samconfig.toml への `[dev.*]` 追加／deploy.yml のトリガー・環境振り分け・concurrency・スモーク対象／github-oidc.yaml の Condition（StringLike 化＋`ai/*` 追加）／project.yaml の `verify` セクション／Amplify アプリ設定（自動ブランチ作成・自動削除・branch env。AWS 側） |
| 変更可能（触れても影響が閉じるもの） | deploy.yml 内コメント／samconfig.toml 内コメント（ASCII）／[7] 対象ドキュメントの該当節 |
| **変更禁止**（外部仕様・共有資産） | prod スタック名 `knowledge-hub`・物理名 3 点・prod API URL（`https://nx7936lj07...`）／DynamoDB の課金モード（PROVISIONED 維持）とキャパシティ値（5/5+5/5）／main push の prod デプロイ条件（paths 含む）と mvn verify → deploy → smoke の流れ／OIDC ロール名・main の信頼（縮小禁止）・sub の ID 埋め込み形式（F-007）／deploy.yml への `environment:` 追加（F-006）／Amplify main ブランチの設定・アプリレベル環境変数・URL／prod の `CorsAllowedOrigin` 値／`amplify.yml`／backend・frontend の全コード（SPA 化禁止・エラー形式維持）／`.ai-flow/flow/` `roles/` `templates/` 等の配布物／template.yaml・samconfig.toml・github-oidc.yaml の ASCII-only（F-005）／長期 AWS アクセスキーの保存禁止 |
| 要確認（判断できずユーザー確認が必要) | ⑨相当＝下記「未解決事項」: OIDC スタック更新と Amplify 設定の実施者（AI 実行可否）／prod チェンジセット事前確認の実施同意 |

## ⑥ リスク判定・規模判定

| 項目 | 判定 | 根拠 |
|------|------|------|
| リスク | **Critical（確定）** | project.yaml `risk.critical` の「CI/CD からの AWS 認証情報の扱い」（OIDC 信頼条件の拡張＝AdministratorAccess ロールの信頼範囲変更）と「インフラ定義のうち課金に影響する変更」（dev スタック新設で DynamoDB プロビジョンド +10RCU/10WCU）に該当 |
| 規模 | **M（確定）** | 変更 5 ファイル＋AWS 側設定。アプリコード変更なし・影響はデプロイ基盤に閉じる（L の「複数画面/機能・DB 波及」には該当しない）。FLOW.md 基準の「複数ファイル・ロジック変更あり」相当 |
| 独立レビュー[5] | **必須** | リスク Critical（High 以上は規模に関わらず必須）。必須観点: 「ai/** が prod スタックへデプロイされる経路がないこと」（AC 異常系）・変更禁止リスト侵害・OIDC 条件の main 巻き添え縮小がないこと |
| 人間レビュー | **必須** | リスク Critical。特に順 2〜3（チェンジセット確認結果・OIDC 更新）は人間の目視確認を挟む |

### [3]テスト先行フェーズの扱い（スキップ提案）

バックエンド・フロントエンドのコード変更が発生せず、変更対象（GitHub Actions / CloudFormation / AWS 側設定）は `mvn test` の枠組みでテストを先行作成できない。AC の検証は「prod チェンジセット事前確認（順 2）」「dev 実デプロイのスモークテスト（workflow 内蔵）」「[6] dev 環境での通し確認」で担保するため、**[3] のスキップを提案する**（承認事項。既存テストの回帰は [4] 完了条件の `mvn -B verify` が CI で引き続き実行される）。

## ⑦ 動作確認の観点（[3]テスト・[6]動作確認の基準）

- 正常系:
  - `ai/dev-env-deploy` push → Actions 起動 → AssumeRole 成功 → `knowledge-hub-dev` デプロイ成功 → スモーク（dev ApiEndpoint の `GET /api/articles`）200
  - Amplify がブランチ環境を作成・ビルドし、ブランチ URL で記事一覧・詳細・作成・編集・削除・検索が通しで動作（データは dev テーブルに入ること）
- 回帰（④影響範囲を引き継いだ他機能への影響確認）:
  - prod チェンジセットが「変更なし」または Modify のみ（Replacement=True・Add/Remove のリソースがない）
  - main push（本件マージ時）で prod デプロイが従来どおり成功し、prod API URL・物理名 3 点・prod フロント URL/env が不変
  - prod フロントの CRUD が引き続き動作（prod DB のデータ不変）
- 異常系:
  - `mvn verify` 失敗時に SAM デプロイへ進まない（dev でも既存挙動を維持）
  - スモーク失敗時に workflow が失敗終了する（dev/prod とも）
  - main・`ai/**` 以外のブランチ push でいかなるデプロイも起動しない。`workflow_dispatch` を想定外 ref で実行した場合は環境解決ステップで失敗しデプロイに進まない（フェイルクローズ）
  - `ai/**` の実行が `--config-env dev` / スタック `knowledge-hub-dev` 以外へ向かわない（Actions ログの sam deploy 引数で確認）
- 境界値:
  - `ai/dev-env-deploy`（1 階層）: Actions・OIDC・Amplify すべて動作
  - `ai/fix/foo`（多階層・任意確認）: Actions トリガー・OIDC は一致（③の調査結果）。Amplify は `ai/**` パターンでの実挙動を設定後に検証し記録
  - `ai/*` ブランチ削除 → Amplify ブランチ環境が自動削除される（dev SAM スタックは残る）
  - 複数 ai ブランチ同時 push → dev グループ内で直列・後勝ち。prod のデプロイとは相互に干渉しない（concurrency グループ分離の確認）
- 権限別: アプリ内権限なし（対象外）。IAM 面は「main・`ai/*` 以外の ref からの AssumeRole が拒否されること」を信頼条件レビューで確認

## ⑧ ドキュメント反映方針（docs.enabled の場合のみ）

### 前例調査（必須）

- `knowledge/precedents.md` ドキュメント記載慣行: 記載なし（初回）。`knowledge/defaults.md`: docs.targets 全 5 対象とも「サンプルなし・既存ファイルの Markdown 書式踏襲」で確定済み（2026-08-14）→ 既存節の書式に合わせて追記する
- 既存ドキュメント調査: `knowledge-hub/README.md` L79-98（CD・OIDC・Amplify 手順の記載あり）／`docs/設計書.md` §10 相当 L305-307（CD・OIDC・Amplify の記述）／`docs/テーブル定義書.md` L13,17（物理テーブル名 `knowledge-hub-articles` を明記）

### 反映要否

| ドキュメント | 要否 | 根拠（該当記載・前例） |
|-------------|------|----------------------|
| Knowledge Hub 設計書（`knowledge-hub/docs/設計書.md`） | 要 | L305-307 の CD 節が「main のみ・OIDC は main 限定」と記載。dev 環境（ブランチ振り分け・`knowledge-hub-dev`・Amplify 自動ブランチ）を追記 |
| テーブル定義書（`knowledge-hub/docs/テーブル定義書.md`） | 要 | 物理名が `${AWS::StackName}-articles` ベースになるため T-01 の名称記載を更新（prod=`knowledge-hub-articles`／dev=`knowledge-hub-dev-articles`、キャパシティ合計 20/25 の注記）。定義の正 template.yaml との同時更新ルール（project.yaml notes）に従う |
| 画面設計書（`knowledge-hub/docs/screens/`） | 不要 | 画面の項目・イベント・遷移に変更なし |
| Knowledge Hub README（`knowledge-hub/README.md`） | 要 | L79 の CD 説明（main 限定）と L26 無料枠根拠（DynamoDB 10/10 前提）の更新、**Amplify 自動ブランチ作成の設定手順（AC 要求の git 管理外手順の記録先として本 README のデプロイ節を提案**＝[7] で確定） |
| ルート README（`README.md`） | 不要 | ディレクトリ構成に変更なし（project.yaml notes の条件に該当せず） |

