# Claude Code アダプタ

`.ai-flow/` 本体を Claude Code から使うための薄い入口。フロー・役割・ナレッジの実体はすべて `.ai-flow/` 側にあり、ここのファイルは参照するだけ（**内容を複製しない**。二重管理を避ける）。

## 導入手順

前提: プロジェクトルートに `.ai-flow/` が導入済みであること。

1. `commands/ai-flow.md` → プロジェクトの `.claude/commands/ai-flow.md` へコピー（`/ai-flow` コマンドになる）
2. `agents/*.md` → `.claude/agents/` へコピー（coder / code-reviewer / test-writer / test-reviewer）
3. `hooks/pretooluse_guard.py` → `.claude/hooks/` へコピー
4. `settings.snippet.json` の hooks 設定を `.claude/settings.json` にマージ
5. `CLAUDE.snippet.md` の内容をプロジェクトの `CLAUDE.md`（無ければ新規作成）に統合

## この構成での役割分担

- **PreToolUse フック**: git commit/push を常に確認（ask）にし、commit 時は禁止パターンLintを先行実行して ERROR ならブロックする（**早期検知層**。最終防壁は git pre-commit フック側）
- **サブエージェント**: [5]独立レビューは code-reviewer サブエージェントで実行される（コンテキスト自動分離）。各エージェント定義は `.ai-flow/roles/` を読むだけの薄いラッパー
- プロジェクト固有のフック（特定ツールの保存禁止等）が必要な場合は `pretooluse_guard.py` の拡張ポイントに追記する
