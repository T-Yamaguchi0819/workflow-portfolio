# ドキュメント反映記録 No1: dev環境デプロイ対応（[7]）

| 項目 | 内容 |
|------|------|
| 実施日 | 2026-08-14 |
| 反映方針 | plan.md ⑧が正（[7]前ゲートでユーザー承認済み）。対象3件、画面設計書・ルート README は変更不要（承認済み） |
| 記載根拠 | 実装ファイル実物（template.yaml / samconfig.toml / deploy.yml / github-oidc.yaml）＋実環境確定値（_state.md「AWS 側作業の実施記録」・verify.md）。推測記載なし |
| 書式 | 既存ファイルの Markdown 書式踏襲（defaults.md 2026-08-14 確定。style YAML なし＝verify_excel_style 対象外） |
| コミット | 未実施（統括対応） |

## 1. 更新したドキュメントと箇所

### 1-1. `knowledge-hub/docs/設計書.md` — §10 デプロイ・CI 設計（CD 節）

- **CD 箇条書き**: トリガーを main / `ai/**` に更新し、ブランチによる環境振り分け（main → prod `knowledge-hub`／`ai/**` → 共有 dev `knowledge-hub-dev`）、想定外 ref のフェイルクローズ、concurrency の prod/dev グループ分離（dev 内直列・後勝ち）、OIDC 信頼が `main`・`ai/*` に拡張された旨を記載
- **「dev 環境(共有・常設)」箇条書きを新設**: 物理名 `${AWS::StackName}` ベース化（prod は従来固定名と同一解決＝置換なし）、dev CorsAllowedOrigin はデフォルト維持（SSR 経由のみ）、Amplify 自動ブランチ作成（`ai/*`・`ai/**`）とブランチ env `API_BASE_URL`（main はアプリレベル prod URL のまま）、ブランチ削除で環境自動削除・dev スタック常設、設定手順は README デプロイ節へのリンクで委譲
- **「バックエンド(手動時)」箇条書き**: dev の手動デプロイ `sam deploy --config-env dev --profile portfolio` を追記

### 1-2. `knowledge-hub/docs/テーブル定義書.md` — 物理名ベース化・キャパシティ注記

- **§1 テーブル一覧**: T-01 物理名を `${AWS::StackName}-articles` に変更し、直下に環境×スタック名×解決結果の対応表を新設（prod=`knowledge-hub`→`knowledge-hub-articles`／dev=`knowledge-hub-dev`→`knowledge-hub-dev-articles`。属性・インデックス定義は全環境共通と明記）
- **§2 見出し**: 「T-01 knowledge-hub-articles 属性定義」→「T-01 ${AWS::StackName}-articles 属性定義」
- **§4 キャパシティ設計**: 合計行を「合計(1 スタックあたり) 10/10」に改め、prod+dev の 2 スタックでアカウント合計 **20 RCU / 20 WCU**（常時無料枠 25 以内）である注記を追加（スタック増設時の超過注意も付記）

### 1-3. `knowledge-hub/README.md` — CD 説明・無料枠根拠・Amplify 設定手順

- **無料枠の根拠（アーキテクチャ節）**: DynamoDB の記述を「prod 10 + 共有 dev 10 = 合計 20RCU/20WCU を割当（25RCU/WCU 枠内）」に更新
- **「AWS へのデプロイ」節冒頭**: 2 環境構成（prod/共有 dev）の概要文と環境対応表（トリガー・スタック・フロントエンド）を新設
- **バックエンド (SAM)**: 自動デプロイ説明を main / `ai/**` の振り分け＋フェイルクローズ＋OIDC（`main`・`ai/*` 限定）に更新。手動デプロイに `--config-env dev` を追記。dev CorsAllowedOrigin デフォルト維持の理由を付記
- **フロントエンド節を prod / dev に分割**: 既存手順は「フロントエンド (prod)」とし、「フロントエンド (dev: Amplify 自動ブランチ作成)」節を新設。**Amplify 設定手順（git 管理外の AWS 側設定）を再現可能なコマンドとして記録**（[7]前ゲートで記載先=README デプロイ節と確定。AC「設定手順のドキュメント記録」に対応）:
  1. `aws amplify update-app`（autoBranchCreation 有効化・patterns `ai/*` `ai/**`・branchAutoDeletion・ブランチ env `API_BASE_URL`=dev API。実施記録どおり appId=d1e1o87p5asykz・実値 URL で記載。ブランチレベル env がアプリレベル(prod URL)を上書きし main は不変である旨、アプリレベル env・main 設定・amplify.yml は変更しない旨を注記）
  2. 設定前に push 済みブランチの手動取り込み（`create-branch` + `start-job RELEASE`。設定後の新規ブランチでは不要と注記）
  3. ブランチ URL 形式（displayName=スラッシュのハイフン置換。例: `ai/dev-env-deploy` → `https://ai-dev-env-deploy.d1e1o87p5asykz.amplifyapp.com`）

## 2. 検証結果

| 検査 | 結果 |
|------|------|
| 書式検査（verify_excel_style） | 対象外（全対象 Markdown・style YAML 未設定。docs.policy=「なし（Markdown を直接更新）」） |
| 記載内容と実装の突合 | deploy.yml（トリガー・case 分岐・concurrency・スモーク）／template.yaml（`!Sub '${AWS::StackName}-articles'` 等 3 点・5/5+5/5）／samconfig.toml dev セクション／github-oidc.yaml（StringLike main+`ai/*`）を実ファイルで確認して記載。Amplify 手順・URL・確定値は _state.md 実施記録・verify.md evidence 16 と一致 |
| 相互参照 | テーブル定義書→設計書 §5 アンカー不変。設計書→README の新規リンク（`../README.md#aws-へのデプロイ`）は README の既存見出しと一致。目次・項番の崩れなし（両文書とも節番号変更なし） |
| 既存記述との整合 | 設計書 §2.1/§5.1・README 構成図の `knowledge-hub-articles` は prod の解決結果として引き続き正確（下記 3. 判断1） |

## 3. 判断記録

1. **設計書 §2.1 構成図・§5.1 見出し・README 構成図の `knowledge-hub-articles` は据え置き**: 承認済みスコープは「設計書は CD 節のみ」。当該記載は prod の物理名として引き続き正しく（`${AWS::StackName}` 化は prod の解決結果を不変に保つ変更）、物理名の環境差はテーブル定義書 §1 の対応表と設計書 CD 節が担う
2. **README の Amplify 手順は実値（appId・dev API URL）で記載**: 手順の汎用化（プレースホルダ化）より再現性を優先。値の取得方法（`aws amplify list-apps`・スタック Output `ApiEndpoint`）も併記し、環境再構築時に追随可能にした
3. **`start-job` を手順に含めた**: plan ③-6 のコマンドは `create-branch` までだが、実施記録（_state.md）では取り込み後のビルド起動に `start-job(RELEASE)` を実行しており、再現手順として必要なため記録した

## 4. precedents.md への追記（手順7）

「ドキュメント記載慣行」へ 2 件追記:

- git 管理外の AWS 側設定手順は knowledge-hub/README.md デプロイ節に記録（設計書は方針のみ・手順は README へ委譲）
- 環境で変わる物理名はテンプレート表記 `${AWS::StackName}-...` を正とし、環境×解決結果の対応表を併記

機械検査可能な書式ルールの新規確定はなし（style YAML への追記提案なし）。

## 5. 未解決事項

- なし（verify.md §7 の申し送り 2 件〈Amplify ブランチ自動削除の実挙動・多階層ブランチの Amplify 実挙動〉は未検証のためドキュメントには断定記載せず、設定値ベースの記述に留めた。実挙動確認後の追記は [8] 以降の申し送りのまま）

## 6. ゲート提示事項（統括→ユーザー）

上記 1. の変更 3 ファイル＋precedents.md 追記 2 件の確認をもって [7] 完了。コミットは統括対応。
