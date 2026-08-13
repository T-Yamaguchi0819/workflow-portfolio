# Codex アダプタ

`.ai-flow/` 本体を OpenAI Codex（CLI／IDE）から使うための薄い入口。フロー・役割・ナレッジの実体はすべて `.ai-flow/` 側にあり、Codex には「どこを読むか」だけを教える。

## 導入手順

前提: プロジェクトルートに `.ai-flow/` が導入済みであること。

1. `AGENTS.snippet.md` の内容をプロジェクトルートの `AGENTS.md` に統合する（無ければこの内容で新規作成）。Codex はセッション開始時に AGENTS.md を自動で読む
2. カスタムプロンプトを導入する（Codex のカスタムプロンプト置き場 `~/.codex/prompts/` へコピー）:
   - `prompts/ai-flow.md` → フロー統括の起動用
   - `prompts/ai-flow-review.md` → [5]独立レビュー専用（**必ず新しいセッションで**使う）
3. git pre-commit フックを導入する（`.ai-flow/guards/hooks/install-git-hooks.(ps1|sh)`）。Codex には PreToolUse 相当のフックがないため、**禁止パターンの強制は git フックが唯一の機械的防壁**になる

## Claude Code との運用差分

- **サブエージェントがない** → フェーズは同一セッション内で順次実行する。コンテキストが長くなったら遠慮なくセッションを切ってよい（`_state.md` と成果物ファイルから再開できる。再開時は `ai-flow` プロンプトを再実行するだけ）
- **[5]独立レビューは必ず新しいセッションで**実行する（実装セッションの続きでレビューさせると独立性が失われる）。レビューセッションでは `ai-flow-review` プロンプトを使い、impl.md を読ませない
- コミット前の確認ダイアログがない → `AGENTS.md` の記述（`git.commit_policy` 準拠。`manual` ならユーザー明示指示時のみ）と pre-commit フックで担保する
