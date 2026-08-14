<!-- テンプレート: [0]初期化で `{work_dir}/{タスク名}/_state.md` としてコピーして埋める。
     本ファイルはフロー全体の状態の正。各フェーズ開始時に必ず読み、終了時に必ず更新する。 -->
# タスク状態: dev環境デプロイ対応

## 基本情報

| 項目 | 内容 |
|------|------|
| タスク名 | dev環境デプロイ対応 |
| モード | 資料なし（ユーザー指示。統括把握の要件概要は下記「要件メモ」参照） |
| ブランチ | workflow-portfolio (リポジトリルート `.`): `ai/dev-env-deploy` |
| Issue | なし（issue_sync 無効） |
| 規模 | M（[2]で確定: 変更5ファイル＋AWS側設定。アプリコード変更なし・影響はデプロイ基盤に閉じる） |
| リスク | Critical（[2]で確定: risk.critical「CI/CD からの AWS 認証情報の扱い」= OIDC 信頼条件拡張、「課金に影響するインフラ変更」= dev スタックで DynamoDB +10RCU/10WCU。[5]独立レビュー必須＋人間レビュー必須） |
| 開始日 | 2026-08-14 |

## 要件一覧

| No | 機能名 | 概要 | 状態 |
|----|--------|------|------|
| 1 | dev環境デプロイ対応 | 開発段階ブランチ(ai/*)を AWS の共有 dev 環境へデプロイ可能にし、[6]動作確認をデプロイ済み dev 環境で行えるようにする | 完了（完了ゲート通過。PR マージ＝人間の最終承認のみ残） |

### AWS 側作業の実施記録（2026-08-14、いずれも事前承認済み・profile=portfolio）

- OIDC スタック `knowledge-hub-github-oidc` 更新完了。IAM 実機確認: sub = StringLike [main, ai/*]、aud = StringEquals 維持
- コミット `5fe7b2e` を `ai/dev-env-deploy` へ push（guards ERROR 0）→ Deploy run 31774597681 成功（AssumeRole・SAM deploy・スモーク 200 すべて通過、3m34s）
- dev スタック `knowledge-hub-dev` 新規作成完了。ApiEndpoint = `https://rfpwpg8xo5.execute-api.ap-northeast-1.amazonaws.com`、テーブル = `knowledge-hub-dev-articles`
- Amplify update-app 完了: autoBranchCreation=true（patterns ai/* + ai/**）、branchAutoDeletion=true、ブランチ用 env API_BASE_URL=dev API。アプリレベル env（prod URL）は不変を確認
- Amplify create-branch `ai/dev-env-deploy`（設定前 push 済みのため手動取り込み）+ start-job(RELEASE, job 1) 実行、ビルド完了待ち

### 要件メモ（統括把握の要件概要。[1]で正式確定する）

- 方針（ユーザー合意済み）: 共有 dev 環境を1本
  - バックエンド = SAM スタック `knowledge-hub-dev`
  - フロントエンド = Amplify 自動ブランチ作成（`ai/*`）
- 変更対象（想定）:
  - `knowledge-hub/infra/template.yaml` のリソース名を `${AWS::StackName}` ベースに変更
  - `knowledge-hub/infra/samconfig.toml` に dev 環境を追加
  - `.github/workflows/deploy.yml` のトリガーに `ai/**` を追加
  - github-oidc.yaml の信頼条件を main + `ai/*` に拡張
  - `.ai-flow/project.yaml` の `verify.method` を dev 環境確認に更新
- 留意: template.yaml / samconfig.toml は ASCII のみ（precedents F-005）。OIDC sub は ID 埋め込み形式・environment 指定とセット設計（F-006/F-007）

## 進捗マトリクス

<!-- ✓=完了 ／ （空欄）=未着手 ／ 🔄=進行中 ／ ➖=スキップ（承認済み） ／ 🛑=エスカレーション中 -->

| No | [0]初期化 | [1]要件/AC | [2]Plan | [3]テスト | [4]実装 | [5]レビュー | [6]動作確認 | [7]ドキュメント | [8]完了 |
|----|----------|-----------|---------|----------|--------|------------|------------|---------------|--------|
| 1 | ✓ | ✓ | ✓ | ➖ | ✓ | ✓ | ✓ | ✓ | ✓ |

<!-- [8]: 2026-08-14 実績記録・ナレッジ化まで完了、完了ゲート（ユーザー承認・コミット要否確認）待ち。実績.md 作成（first_pass=true・rework 0・ai_findings_effective 2・human_findings 0・escalations 0。工数系3項目は未計測のため null）。precedents.md へ P-001〜P-003（チェンジセット実機確認／OIDC StringLike 完全一致評価／Amplify 自動ブランチ作成の発火条件）と F-008（SAM CLI 未導入の誤検出）を追記。defaults.local.md へ SAM CLI 導入済み(1.152.0)を追記。evaluate_flow.py は完了タスク数1 < review_cycle(10) のため実行不要。一時成果物の削除候補なし（evidence/ は verify.md 参照の恒久エビデンス） -->

<!-- [7]: 2026-08-14 完了。設計書.md §10 CD 節・テーブル定義書.md（物理名テンプレート表記+環境対応表+キャパシティ 20/25 注記）・knowledge-hub/README.md（2環境構成・CD 振り分け・Amplify 設定手順）を更新。precedents.md に記載慣行2件追記。詳細は No1_dev環境デプロイ対応/docs.md -->

<!-- [6]: 2026-08-14 PASS。mvn test 16件全PASS。dev API CRUD/検索/エラー形式・dev フロント SSR（全ページ200・API データ反映・クエリURL）・prod 回帰（データ/URL 不変・テーブル分離）を curl + AWS CLI(read-only) で確認。エビデンス evidence/（対応表・判断記録は No1_dev環境デプロイ対応/verify.md）。テスト記事1件「dev 動作確認用 (SSR検証 verify-20260814)」を dev テーブルに残置（verify.md §6 に判断記録）。申し送り3件: main マージ時の prod デプロイ確認／Amplify ブランチ自動削除の実挙動／多階層ブランチの Amplify 実挙動（任意）＝verify.md §7 -->

<!-- [5]: 2026-08-14 PASS(初回・往復0)。推奨指摘2件(コメント乖離)は対応済み。詳細は review.md。prod 無置換の事前検証も完了: sam deploy --no-execute-changeset で changeset 確認 → ApiFunction の Modify(Code のみ・ローカル再ビルド jar のハッシュ差)+ AutoPublishAlias の Version 回転のみ。FunctionName/テーブル/HttpApi は差分なし・Replacement なし → 命名変更起因の差分ゼロを実機確認。チェンジセットは削除済み -->

<!-- [3]: スキップ（2026-08-14 ユーザー承認済み。アプリコード変更なし。検証はチェンジセット確認＋デプロイ内蔵スモーク＋[6]で代替） -->
<!-- [4]: 2026-08-14 完了。ファイル変更5点（template.yaml/samconfig.toml/deploy.yml/github-oidc.yaml/project.yaml）。自己チェック: ASCII OK・cfn-lint 0件（SAM CLI 未導入のため代替）・guards ERROR 0・スコープ外変更なし。詳細は No1_dev環境デプロイ対応/impl.md。AWS側操作（実施順序2〜5）とコミットは未実施（統括対応） -->

## 解決済みの確認事項

- 2026-08-14 dev 環境の構成方針: 共有 dev 環境1本（SAM `knowledge-hub-dev` + Amplify 自動ブランチ `ai/*`）で合意済み（統括より）
- 2026-08-14 ドキュメント名義人: `T-Yamaguchi0819`（GitHub ユーザー名をそのまま使用）（ユーザー回答）
- 2026-08-14 ローカル環境情報: `.claude/CLAUDE.md` の開発機固有情報（JDK21 パス・ポート 8081）を defaults.local.md へ転記してよい（ユーザー回答）
- 2026-08-14 ドキュメント書式: docs.targets 全5対象とも「サンプルなし・既存ファイルの書式踏襲」。以後のタスクで再確認不要（ユーザー回答。defaults.md へ記録する）
- 2026-08-14 **AC 承認**: No1 要件.md の Acceptance Criteria をユーザーが承認（承認者 T-Yamaguchi0819、要件.md の承認記録に記入済み）。設計前提3点（dev CORS はデフォルト値のまま／dev SAM スタックは常設／多階層ブランチの一致範囲確認は [2]Plan に委譲）も同時に確定
- 2026-08-14 **Plan 承認**: plan.md（修正方針・変更分類・リスク Critical／規模 M）をユーザーが承認
- 2026-08-14 [3]テスト先行のスキップをユーザーが承認（検証はチェンジセット確認＋デプロイ内蔵スモーク＋[6]で代替）
- 2026-08-14 AWS 側操作（OIDC スタック更新・Amplify update-app/create-branch）は **AI が profile=portfolio で実行してよい**（各実行前に内容を報告する条件付き）（ユーザー回答）
- 2026-08-14 prod 無置換の事前検証 `sam deploy --no-execute-changeset --profile portfolio`（チェンジセット作成のみ・実行せず削除）のローカル実施に同意（ユーザー回答）
- 2026-08-14 **[5]ゲート通過**: レビュー結果（PASS・推奨2件対応済み）とチェンジセット検証結果を了承。**OIDC スタック更新→コミット&push→dev 初回デプロイ→Amplify 設定への進行を承認（コミット/push の明示指示を含む）**（ユーザー回答）
- 2026-08-14 **[7]前ゲート通過**: [6]PASS の結果を了承し、[7]ドキュメント反映（設計書 CD 節／テーブル定義書の物理名・キャパシティ注記／knowledge-hub README の CD・無料枠・**Amplify 設定手順の記載先=README デプロイ節で確定**）への進行を承認（ユーザー回答）

## 未解決の確認事項

- なし（完了ゲート 2026-08-14 通過。最終承認は PR マージ＝人間が行う）

### 完了ゲートの回答記録（2026-08-14）

- コミット/PR: **docs スコープとフロー成果物の2コミットに分割して push し、main への PR を作成する**ことを承認（マージはユーザー）
- 実績.md の工数値: null のままでよい（未計測のため。推測値記入禁止に従う）
- AWS 側操作の運用: 「AI が profile=portfolio で実行可（実行前報告付き）」を**恒久デフォルト化**（defaults.md に記録済み。prod リソースの置換・削除を伴う操作は対象外として都度確認）
- dev テーブルの検証用記事1件: 残置でよい

## 適用したデフォルト（事後報告済み）

- [x] flow.size_default: M を暫定規模として適用（project.yaml）→ [2]で M 確定・報告済み
- [x] ブランチ名は ASCII（`ai/dev-env-deploy`）を採用（AC 承認ゲートで事後報告済み）
