# 動作確認記録 No1: dev環境デプロイ対応（[6]）

| 項目 | 内容 |
|------|------|
| 実施日 | 2026-08-14 |
| 実施方法 | curl（dev/prod の API・フロントエンド HTML）＋ AWS CLI read-only 照会（profile=portfolio）＋ `mvn test`（回帰）。ブラウザ操作なし（統括指示） |
| 対象環境 | dev API `https://rfpwpg8xo5.execute-api.ap-northeast-1.amazonaws.com`（スタック knowledge-hub-dev）／dev フロント `https://ai-dev-env-deploy.d1e1o87p5asykz.amplifyapp.com`／prod は回帰の read-only 参照のみ |
| エビデンス | `.ai-flow/work/dev環境デプロイ対応/evidence/`（ファイル番号は下表の (NN) に対応。HTTP ステータス一覧は `30_http-status-summary.txt`） |
| 結果 | **PASS**（[6] で確認可能な AC 全項目充足。確認不能 2 項目は後続フェーズへ申し送り＝下記「残課題」） |

## 1. 自動テスト（回帰）

- `mvn test`（knowledge-hub/backend、JDK21）: **Tests run: 16, Failures: 0, Errors: 0, Skipped: 0 / BUILD SUCCESS**（evidence `00_mvn-test.log`）
- [3] は承認済みスキップのため新規テストなし。既存回帰のみ。CI（run 31774597681）でも `mvn verify` 通過済み（`18_deploy-run-31774597681.txt`）

## 2. dev API の CRUD・検索通し（plan ⑦ 正常系）

初期状態は空テーブル（`GET /api/articles` → 200 `[]`、evidence 01）。以降すべて実測 200 系:

| 操作 | 結果 | evidence |
|------|------|----------|
| POST 作成 | 201。id 採番・createdAt/updatedAt 付与 | 02 |
| GET 一覧（作成後） | 200・1件。作成タイトルを含む | 03 |
| GET 詳細 | 200 | 04 |
| PUT 更新 | 200。title/tags 反映・updatedAt のみ更新（createdAt 不変） | 05 |
| GET `?q=ヤマビコ`（キーワード） | 200・1件ヒット | 06 |
| GET `?category=検証`（カテゴリ＝GSI 経路） | 200・1件ヒット | 07 |
| GET `?q=存在しない語` | 200・`[]`（0件） | 07b |
| DELETE | 204。再取得 404・一覧 200 `[]` | 09 / 09b |

エラーレスポンス形式（AC「変更してはいけない既存仕様」）:

- POST title 空 → **400** `{"message":"入力内容に誤りがあります","errors":["title: タイトルは必須です"]}`（evidence 08）
- 削除後 GET → **404** `{"message":"記事が見つかりません: ...","errors":[]}`（evidence 09b）
- → `{"message","errors"}` 形式維持を確認

## 3. dev フロントエンド SSR 確認（Amplify ブランチ環境）

SSR 確認用記事を dev API に作成（201、id=c24e3379-...、evidence 20）した上で、curl で HTML を取得:

- `/` → 307 → `/articles`（`app/page.tsx` の redirect 仕様どおり。追従後 200、evidence 21/21b）
- `/articles`・`/articles/{id}`・`/articles/new`・`/articles/{id}/edit` → すべて **200**（evidence 22-25）
- SSR 描画への API データ反映: 一覧・詳細・編集の各 HTML に作成記事タイトル「dev 動作確認用 (SSR検証 verify-20260814)」と本文キーワードが**含まれる**ことを確認（`cache: "no-store"` の SSR が dev API を参照している実証。evidence 22/23/25）
- クエリ付き URL: `/articles?q=ヤマビコ`（ヒット）・`/articles?category=検証`（ヒット）・`/articles?q=存在しない語`（タイトル非含有＝0件表示）すべて 200（evidence 26-28/26b）
- ブランチ env: `aws amplify get-branch ai/dev-env-deploy` → `API_BASE_URL = dev API`。main はブランチ env なし（アプリレベル= prod URL）。autoBranchCreation=true（patterns ai/* + ai/**）・branchAutoDeletion=true・productionBranch=main（evidence 16）

※ AC の「作成・編集・削除が dev API（SSR 経由）で動作」は、統括指示（curl ベース・ブラウザ操作不要）に基づき「API レベルの CRUD 実証（§2）＋新規/編集ページの 200 表示＋SSR 描画へのデータ反映」の組合せで充足と判断した。Server Actions のフォーム送信そのものはブラウザ E2E でのみ実行可能（残課題ではなく確認方法の割り切りとして記録）。

## 4. 回帰確認（prod・read-only）

- prod API `GET /api/articles`: dev 操作の前後で **200・1件・同一 id（f77ef089-...）・レスポンスボディ完全一致**（evidence 10/11）
- prod API に dev 記事 id を GET → **404**（evidence 12）
- prod フロント `/articles` → 200。prod 記事タイトル表示あり・**dev 記事タイトルは含まれない**。詳細ページも 200（evidence 13/14）
- DynamoDB 実テーブル分離: dev 記事は `knowledge-hub-dev-articles` に存在し、`knowledge-hub-articles`（prod）には**存在しない**（get-item 空）。scan COUNT は prod=1・dev=1（evidence 15）
- キャパシティ: 両テーブルともテーブル 5/5 + GSI(category-index) 5/5 のプロビジョンド → 合計 20RCU/20WCU ≤ 25（無料枠内。evidence 17）
- dev スタック: CREATE_COMPLETE、`CorsAllowedOrigin=http://localhost:3000`（テンプレートデフォルト維持）、Outputs に ApiEndpoint/TableName（evidence 17）

## 5. AC 対応表

| AC（要件.md） | 結果 | エビデンス |
|---------------|------|-----------|
| ai/** push → Actions 起動・AssumeRole 成功・knowledge-hub-dev デプロイ | ✅ Deploy run 31774597681 成功（3m34s） | 18、_state.md 実施記録 |
| dev スモーク: ApiEndpoint の GET /api/articles が 200 | ✅ run 内蔵スモーク通過＋本フェーズ実測 200 | 18、01 |
| main push → 従来どおり prod へデプロイ | ⏭ 本件未マージのため実 push は未発生。prod 不変（URL・データ・物理名）は確認済み。**マージ時の prod デプロイ成功確認を [8]/マージ後に実施** | 10/11/13/17 |
| prod で置換・再作成・削除が発生しない | ✅ [5] チェンジセット検証（Modify のみ・Replacement なし）＋本フェーズで prod API/フロント URL 稼働・データ不変を確認 | _state.md [5] 記録、10-14 |
| dev 物理名 knowledge-hub-dev-articles 等で prod と衝突しない | ✅ dev スタック Outputs・describe-table で実在確認。prod テーブルと別実体 | 15/17 |
| Amplify: ai/* ブランチ環境の URL で一覧・詳細・作成・編集・削除・検索が dev API 経由で動作 | ✅（§3 の確認方法による。全ページ 200・SSR 反映・API CRUD/検索通し） | 20-28、02-09 |
| Amplify: ブランチ削除で環境自動削除 | ⏭ 未検証（ブランチはタスク完了まで存続）。設定値 `enableBranchAutoDeletion=true` は確認済み。**実挙動はマージ後のブランチ削除時に確認** | 16 |
| branch env API_BASE_URL=dev API／main は prod のまま | ✅ get-branch/get-app 照会で実証 | 16 |
| dev CorsAllowedOrigin はデフォルト値のまま・prod 値不変 | ✅ dev スタック Parameters=`http://localhost:3000`。prod は samconfig default 無変更（[5]確認） | 17 |
| project.yaml verify.method が dev 環境確認に更新 | ✅ 本フェーズ自体が更新後の method に従い dev 環境で実施 | project.yaml L62 |
| DynamoDB 合計 20/20 ≤ 25 | ✅ describe-table 実測（prod 5/5+5/5、dev 5/5+5/5） | 17 |
| Amplify 設定手順のドキュメント記録 | ⏭ [7] で対応（記載先候補 knowledge-hub/README.md デプロイ節） | — |
| 境界値: ai/dev-env-deploy（1階層）が全経路動作 | ✅ Actions・OIDC・Amplify すべて実証 | 18/16/21-28 |
| 境界値: 多階層 ai/a/b の Amplify 実挙動 | ⏭ 任意項目・未検証（バックエンド経路は [5] で確実と確認済み。Amplify は ai/** パターン登録済み） | 16 |
| 異常系: エラー形式 {"message","errors"} 維持 | ✅ 400/404 とも形式維持 | 08/09b |
| 異常系: mvn verify 失敗・スモーク失敗・想定外 ref のフェイルクローズ | ✅ 構造確認（[5] レビュー・impl 自己チェックのシミュレーション）。実発生なし | review.md 必須観点 1 |

## 6. テストデータの扱い（判断記録）

- CRUD 検証用の 1 件目（aea36ac9-...）は DELETE 検証を兼ねて**削除済み**
- SSR 確認用の 1 件（id=c24e3379-...、タイトル「dev 動作確認用 (SSR検証 verify-20260814)」、カテゴリ「検証」）は **dev テーブルに残す**と判断した
  - 理由: 今後の [6] 動作確認・スモーク時に非空状態のベースラインとして有用／プロビジョンド課金のため件数によるコスト影響なし／タイトルで検証用データと明示済み。不要になれば dev テーブルは自由に削除してよい（統括指示で dev テーブルのデータ操作は許可済み）

## 7. 残課題（後続フェーズへの申し送り）

1. **main マージ時の prod デプロイ成功確認**（AC「main push → 従来どおり prod」）: マージ後に Actions run と prod スモークの成功、prod API URL 不変を確認する
2. **Amplify ブランチ自動削除の実挙動確認**: `ai/dev-env-deploy` 削除時にブランチ環境が消えることを確認し、結果をドキュメント（[7] 記載先）へ反映
3. 多階層ブランチ（`ai/a/b`）の Amplify 自動作成は任意項目のため未検証（次に多階層ブランチを使う機会に確認して記録）

失敗・修正は発生していない（3回ルール適用なし・[5] 再レビュー不要）。
