# workflow-portfolio

このリポジトリには 2 つの成果物が同居しています。

| ディレクトリ | 内容 |
|--------------|------|
| `.ai-flow/` `adapters/` `docs/` | **ai-dev-flow** — AI支援修正フローの汎用パッケージ (本ページ下記) |
| [`knowledge-hub/`](knowledge-hub/README.md) | **Knowledge Hub** — ポートフォリオ用の動的Webアプリ (Next.js SSR + Spring Boot 3 + DynamoDB / AWS無料枠サーバーレス構成) |

---

# ai-dev-flow — AI修正フロー汎用パッケージ

複数のコーディングエージェント（**Claude Code / Codex / Cursor** 等）で共通に使える、AI支援修正フローの配布パッケージ。本番稼働中レガシーシステムの保守運用（安全ポータル `anzen-pc-fix`）で構築した仕組みを、プロジェクト非依存に汎用化したもの。

## 設計原則

1. **本体はエージェント中立** — フロー定義・役割定義・テンプレート・ナレッジはすべて素の Markdown と設定ファイル。特定エージェントの機能（サブエージェント・フック・スキル）に依存しない。エージェント固有の部分は `adapters/` の薄い入口だけ
2. **状態はファイルで持つ** — `_state.md` と成果物ファイルの受け渡しで各フェーズが自己完結する。コンテキスト消失・セッション切替・**エージェントの乗り換え**（実装は Claude Code、レビューは Codex 等）に耐える。人間向けの可視化が必要な場合は GitHub Issue へ進捗を**ミラー**できる（`project.yaml` の `issue_sync`。正はあくまでファイル）
3. **強制は git で行う** — 禁止パターン検査（`guards/verify_diff.py`）は git pre-commit フックとして導入し、**どのエージェント経由のコミットでも機械的に作動**させる。エージェント固有フック（Claude Code の PreToolUse 等）は追加の早期検知層。最終承認も git に置ける（`commit_policy: auto`: フェーズごとに自動コミットし、PR マージ＝人間を承認ポイントにする3層レビュー）
4. **AI が間違えても検出できる構造** — Acceptance Criteria の事前固定・独立レビュー（実装者の思考過程を見せない）・決定論的ガード・失敗事例のナレッジ化→ルール化サイクル

## 構成

```
ai-dev-flow/
├── .ai-flow/                    ← 対象プロジェクトのルートへコピーする本体
│   ├── FLOW.md                  # フロー統括（フェーズ・S/M/L分岐・ゲート・状態管理）
│   ├── project.yaml             # プロジェクト適用設定（導入時に必ず編集）
│   ├── check_env.py             # 導入前提チェック（設定に応じた必要ツールの過不足を表示）
│   ├── evaluate_flow.py         # フロー評価レポート（実績集計・KPI判定・傾向・要注意タスク）
│   ├── flow/                    # フェーズ定義 0-init 〜 8-finalize
│   ├── templates/               # _state.md／要件.md（AC含む）／plan.md／実績.md
│   ├── roles/                   # coder / code-reviewer / test-writer / test-reviewer
│   ├── knowledge/               # defaults（運用値）／precedents（判断履歴DB）
│   ├── docs-style/              # ドキュメント書式（style YAML＝検証用＋雛形 .xlsx＝生成用）
│   └── guards/                  # 禁止パターンLint＋Excel書式の抽出/検査スクリプト
│       └── hooks/               # git pre-commit テンプレート＋インストーラ
├── adapters/
│   ├── claude-code/             # .claude/ 用（コマンド・エージェント・PreToolUseフック）
│   ├── codex/                   # AGENTS.md スニペット＋カスタムプロンプト
│   └── cursor/                  # .cursor/ 用（rules .mdc＋commands）
└── docs/
    └── 導入ガイド.md            # ステップバイステップの導入手順
```

## 対応エージェント

| 機能 | Claude Code | Codex | Cursor |
|------|------------|-------|--------|
| フロー起動の入口 | `/ai-flow` コマンド | カスタムプロンプト | `.cursor/commands` |
| ルール自動適用 | CLAUDE.md（スニペット統合） | AGENTS.md（スニペット統合） | AGENTS.md／`.mdc` |
| フェーズのコンテキスト分離 | サブエージェント | 別セッションで実行 | 別チャットで実行 |
| 独立レビュー | reviewer サブエージェント | 別セッション＋レビュープロンプト | 別チャット＋レビューコマンド |
| 禁止パターン強制 | git pre-commit＋PreToolUseフック | git pre-commit | git pre-commit |

どのエージェントでも**フロー定義・成果物・ナレッジは同一ファイルを共有**する。エージェントを混在させても（例: 実装 Claude Code／レビュー Codex）状態はファイル経由で引き継がれる。

## クイックスタート

```
1. .ai-flow/ を対象プロジェクトのルートへコピー
2. .ai-flow/project.yaml を編集（技術スタック・コマンド・コミット書式・リスク分類）
3. .ai-flow/guards/guard-rules.json に禁止パターンを定義
4. .ai-flow/guards/hooks/install-git-hooks.(ps1|sh) で pre-commit を導入
5. 使うエージェントの adapters/ をコピー（各 README 参照）
6. エージェントで修正フローを起動（例: Claude Code なら /ai-flow <タスク名>）
```

詳細は [docs/導入ガイド.md](docs/導入ガイド.md) を参照。

## フローの概要

```
0 初期化 → 1 要件確認＋AC固定 → 2 調査・Plan（変更分類・リスク/規模判定）
        → 3 テスト先行作成 → 4 実装 → 5 独立レビュー → 6 動作確認
        → 7 ドキュメント反映 → 8 実績記録・ナレッジ化・完了
```

- **規模 S/M/L でフェーズを分岐**する（軽微な修正にフルフローを強制しない）。リスク High/Critical の変更は規模に関わらず独立レビュー必須
- **Acceptance Criteria（期待結果・境界値・異常系・禁止事項・不変仕様）を人間が承認してから**テスト・実装に進む。AI が書いたテストは AC を満たすための実装物として扱う
- **独立レビューは実装とコンテキストを分離**して行う（レビュアーには要件・AC・Plan・diff のみを見せ、実装者の作業記録・思考過程を見せない）
- 各案件で**実績（人間工数・手戻り回数・初回PASS率等）を記録**し、失敗事例は `knowledge/precedents.md` → `guard-rules.json` のルール化サイクルへ流す

## 思想

> 一番重要なのは「AI をもっと賢くする」ことではなく、「AI が間違えても検出できる構造」と「失敗を次回に活かす構造」を作ること。

このパッケージが提供するのはプロンプト集ではなく、**AC 固定・独立レビュー・決定論的ガード・ナレッジ蓄積**という 4 つの検出/改善構造である。エージェントや LLM が変わっても、この構造はファイルとして残り続ける。
