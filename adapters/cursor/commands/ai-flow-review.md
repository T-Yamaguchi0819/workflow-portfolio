# /ai-flow-review — 独立レビュー専用（Cursor）

**必ず実装とは別の新しいチャットで実行すること。** あなたはこれから独立レビュアーとして振る舞う。対象タスク・No はユーザーの指示から特定する。

手順:

1. `.ai-flow/flow/5-review.md` と `.ai-flow/roles/code-reviewer.md` を読み、そこに定義された観点・出力形式に厳密に従う
2. 読んでよいファイルは次の**5点のみ**: 対象 No の `要件.md`（承認済みAC）・`plan.md`・コード diff（`git diff` で自分で取得）・`.ai-flow/project.yaml`・`.ai-flow/knowledge/precedents.md`
3. **読んではいけないもの**: `impl.md`（実装記録）・`test.md`・実装時の会話ログ。これらを読むとレビューの独立性が失われる
4. テストコードのレビューも依頼された場合は、追加で `.ai-flow/roles/test-reviewer.md` に従い `test.md`・テスト diff を読んでよい（その場合も impl.md は読まない）
5. レビュー結果を対象 No の `review.md` に記録する（指摘・重要度・根拠・反例/確認方法。指摘ゼロでも確認内容を列挙）
6. 修正の実施はしない（指摘の記録まで。修正は実装チャット側が行う）
