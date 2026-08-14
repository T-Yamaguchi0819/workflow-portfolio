# レビュー記録 No1: dev環境デプロイ対応（[5] 独立レビュー）

| 項目 | 内容 |
|------|------|
| レビュー実施日 | 2026-08-14 |
| レビュアー | code-reviewer（独立・実装記録 impl.md 不参照） |
| 入力 | 要件.md（承認済み AC）／plan.md／`git diff main`（未コミット作業ツリー）／project.yaml／knowledge/precedents.md |
| 対象 diff | template.yaml／samconfig.toml／deploy.yml／github-oidc.yaml／.ai-flow/project.yaml（＋plan 外: .ai-flow/knowledge/defaults.md） |
| 判定 | **PASS（要修正なし）**。推奨 2 件・備考 1 件・未解決事項 3 件 |
| 往復回数 | 0（初回 PASS） |

## 指摘一覧

### 推奨1: github-oidc.yaml 内の説明文が「main のみ」のまま（実態と乖離）

| 項目 | 内容 |
|------|------|
| 重要度 | 推奨（改善提案。マージ可） |
| 対象 | knowledge-hub/infra/github-oidc.yaml:5-6（テンプレート Description「main branch of the specified repository」）、:43（Role Description「main branch only」）、:66-68（コメント「limited to one repo/branch」） |
| 指摘 | 信頼条件は main + ai/* に拡張されたが、説明文・コメントが「main のみ」のまま。将来の運用者が信頼範囲を誤認するおそれ |
| 根拠 | plan ⑤「変更可能: コメント」。機能影響なし（説明文のみ）。ただし Role の `Description` プロパティ修正は plan ③-4「その他プロパティは変更しない」に触れるため、直すのはテンプレート Description とコメントに留めるか、統括判断とする（いずれも Modify のみで置換は発生しない） |
| 反例/確認方法 | 目視。ASCII のみで修正すること（F-005） |

### 推奨2: deploy.yml の NOTE コメントの信頼条件記述が古い

| 項目 | 内容 |
|------|------|
| 重要度 | 推奨（軽微） |
| 対象 | .github/workflows/deploy.yml:33-35 |
| 指摘 | 「IAM ロールの信頼条件 (ref:refs/heads/main)」の記載が拡張後（main + ai/*）と不一致。Environment 禁止の注意書き自体は引き続き正しい |
| 根拠 | plan ⑤「変更可能: deploy.yml 内コメント」。ドキュメント整合のみ |
| 反例/確認方法 | 目視 |

### 備考1: plan の対象ファイル一覧に無い defaults.md の変更が diff に含まれる

| 項目 | 内容 |
|------|------|
| 重要度 | 備考 |
| 対象 | .ai-flow/knowledge/defaults.md |
| 指摘 | plan ② の 5 ファイル外の変更。内容はドキュメント書式デフォルトの確認記録（2026-08-14 確定）であり、plan ⑧が「確定済み」として参照している事項の記録そのもの。フロー運用上の knowledge 追記であり実装スコープ外変更には当たらないと判断 |
| 根拠 | constraints の配布物禁止対象は「.ai-flow/flow/ roles/ templates/ 等」で knowledge/ は導入先が追記する設計（precedents.md に F-001〜F-007 が既に記録済みの慣行と整合）。AC 禁止事項にも非抵触 |
| 反例/確認方法 | — |

## 必須観点の確認結果（問題なしとした根拠）

1. **ai/** → prod スタックへの経路なし（AC 異常系・最重要）**
   - トリガーは `branches: [main, 'ai/**']` のみ。環境解決ステップ（deploy.yml:39-52）が `case "${GITHUB_REF}"` で main→`default`/`knowledge-hub`、`refs/heads/ai/*`→`dev`/`knowledge-hub-dev` を固定し、それ以外は `exit 1`（フェイルクローズ。`workflow_dispatch` を想定外 ref で実行してもデプロイに進まない）
   - `sam deploy --config-env dev` の対象は samconfig.toml `[dev.deploy.parameters]` の `stack_name = "knowledge-hub-dev"` に固定。ai/** 実行が prod（`knowledge-hub`）へ向かう経路は構造上存在しない
   - スモークテストの `describe-stacks` も `steps.env.outputs.stack_name` で振り分け済み
   - シェル case の `*` は `/` を跨いで一致するため `ai/fix/foo`（多階層）も dev 側に解決（plan ③調査結果と整合）
   - concurrency はグループ分離（`-prod`/`-dev`）＋ `cancel-in-progress: false` 維持 → prod/dev の相互キャンセルなし、dev 内直列・後勝ち（AC 境界値と整合）

2. **変更禁止リスト（plan ⑤）の非侵害**
   - 物理名 3 点: `!Sub '${AWS::StackName}-articles'` 等はスタック名 `knowledge-hub` で `knowledge-hub-articles`／`knowledge-hub-api`／`knowledge-hub-http-api` に解決され現行と完全一致（CFn は解決後の値で差分判定 → 置換なしの想定。最終確証は未解決事項1のチェンジセット確認）
   - DynamoDB: `BillingMode: PROVISIONED`・テーブル 5/5・GSI 5/5 とも不変。dev 追加で合計 20/20 ≤ 25（無料枠内）
   - samconfig `[default.*]`（stack_name・prod CorsAllowedOrigin の parameter_overrides 含む）は無変更。dev セクションに parameter_overrides なし → dev CORS はデフォルト `http://localhost:3000`（AC どおり）
   - deploy.yml: paths 条件・mvn verify → deploy → smoke の順序不変。`environment:` 指定なし（F-006 遵守）。長期アクセスキーなし・秘密情報ハードコードなし
   - template.yaml に他の固定物理名は残存せず（dev スタック新設時の名前衝突なし）。amplify.yml・backend/frontend コード・`.ai-flow/flow/ roles/ templates/` は diff に含まれない

3. **OIDC: main の信頼が縮小しないこと**
   - main の sub 値は変更前と同一文字列を `StringLike` のリスト先頭に保持。IAM の StringLike はワイルドカード非含有値を完全一致として評価するため main の信頼は意味論的に不変（縮小なし）。リスト複数値は OR 評価で `ai/*` が追加されるのみ
   - `aud` は `StringEquals` のまま。sub は ID 埋め込み形式（owner@ownerId/repo@repoId）を維持（F-007 遵守）。`RoleName: knowledge-hub-github-deploy` 不変（Modify 更新・置換なし）
   - IAM の `*` は `/` にも一致するため `ai/fix/foo` も許可（plan の一致範囲表と整合）。main・ai/* 以外の ref は不一致で AssumeRole 拒否

4. **ASCII 検査（F-005）**: template.yaml／samconfig.toml／github-oidc.yaml の 3 ファイルを機械検査（`grep -P '[^\x00-\x7F]'`）し、非 ASCII 文字なしを確認

5. **AC 反例探索（その他）**
   - dev 初回スモーク＝空テーブル: `DynamoDbArticleRepository` の scan は空リストを返し `GET /api/articles` は 200 + `[]`（反例なし）
   - `--config-env default` の明示は従来の暗黙 default と同一挙動（main の prod デプロイ不変）
   - project.yaml は `verify` セクションのみ変更（method・local_env コメント）。plan ③-5 の文言どおり
   - precedents F-001〜F-007 と同型の誤りなし

## 未解決事項（レビューでは判定不能。統括→ユーザーへ）

1. **prod 空チェンジセット事前確認（plan 実施順序 2）が未実施**: AC「prod で置換・再作成・削除が一切発生しない（changeset が Modify のみ、または空）」の最終確証は `sam deploy --no-execute-changeset --profile portfolio`（default 環境）での実機確認が必要。diff 上は解決値同一で差分なしの論理確認まで。**マージ前に必須**（人間レビュー対象。リスク Critical）
2. **Amplify 関連 AC（自動ブランチ作成・自動削除・branch env API_BASE_URL・main 不変）は git 管理外の AWS 側設定のため本 diff に現れず未検証**。plan 実施順序 5 の実施後、[6] で検証すること
3. **OIDC スタック更新・Amplify 設定の実施者（AI 実行可否）**: plan ⑤「要確認」のまま未確定。ユーザー承認が必要（リスク Critical につき人間レビュー必須）

## 対応記録

- **推奨1: 対応済み（2026-08-14・実装者）**。github-oidc.yaml のテンプレート冒頭 Description を「main branch (prod) or ai/* branches (shared dev)」に、末尾コメントを「limited to one repo (main and ai/* branches only)」に修正（ASCII のみ維持を再検査済み）。**`DeployRole` の `Description` プロパティ（「main branch only」）は据え置き**: 統括判断により plan ③-4「その他プロパティは変更しない」を優先（プロパティ変更は IAM ロールの Modify 更新を伴うため、機能影響なしの文言乖離は許容。将来 OIDC スタックを別件で更新する際に併せて修正すればよい）。修正後 cfn-lint 指摘 0 件
- **推奨2: 対応済み（2026-08-14・実装者）**。deploy.yml:33-36 の NOTE コメントの信頼条件記述を「(ref:refs/heads/main と ref:refs/heads/ai/*)」に修正。YAML パース再確認 OK
- 備考1: 対応不要（レビュアー判断どおり knowledge/ への追記はフロー運用上の記録でありスコープ外変更に当たらない）
- 未解決事項 1〜3: 統括→ユーザーで処理（plan 実施順序 2〜5 の実機作業。本対応記録の対象外）
