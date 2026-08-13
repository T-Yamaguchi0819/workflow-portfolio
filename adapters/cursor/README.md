# Cursor アダプタ

`.ai-flow/` 本体を Cursor から使うための薄い入口。フロー・役割・ナレッジの実体はすべて `.ai-flow/` 側にあり、Cursor には「どこを読むか」だけを教える。

## 導入手順

前提: プロジェクトルートに `.ai-flow/` が導入済みであること。

1. `rules/ai-flow.mdc` → プロジェクトの `.cursor/rules/ai-flow.mdc` へコピー（常時適用ルールとして `.ai-flow/` の存在と参照先を教える）
   - Cursor は `AGENTS.md` もサポートしているため、`.mdc` の代わりに `adapters/codex/AGENTS.snippet.md` を `AGENTS.md` に統合する方法でもよい（チームで Codex と併用するならこちらに寄せると一元管理できる）
2. コマンドを導入する（`.cursor/commands/` へコピー）:
   - `commands/ai-flow.md` → フロー統括の起動用（チャットで `/ai-flow` と入力）
   - `commands/ai-flow-review.md` → [5]独立レビュー専用（**必ず新しいチャットで**実行）
3. git pre-commit フックを導入する（`.ai-flow/guards/hooks/install-git-hooks.(ps1|sh)`）。禁止パターンの機械的強制は git フックが担う

## Claude Code との運用差分

- **サブエージェントがない** → フェーズは同一チャット内で順次実行する。長くなったら新しいチャットで再開してよい（`_state.md` から復元される）
- **[5]独立レビューは必ず新しいチャットで** `/ai-flow-review` を実行する（実装チャットの続きでレビューさせない）
- コミットは `git.commit_policy` 準拠。`manual` ならユーザー明示指示時のみ（ルール記述と pre-commit フックで担保）
