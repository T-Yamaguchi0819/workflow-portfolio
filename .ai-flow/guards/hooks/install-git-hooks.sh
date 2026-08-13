#!/bin/sh
# ai-dev-flow: git pre-commit フックのインストーラ（macOS / Linux / Git Bash）
# 使い方:
#   ./install-git-hooks.sh [-f] [repo_path ...]
#     repo_path 省略時は guard-rules.json の repos（プロジェクトルート相対）へ導入
#     -f: 既存の pre-commit を上書き
set -e

hooks_dir="$(cd "$(dirname "$0")" && pwd)"
guards_dir="$(dirname "$hooks_dir")"
verify_diff="$guards_dir/verify_diff.py"
template="$hooks_dir/pre-commit"
project_root="$(dirname "$(dirname "$guards_dir")")"

force=0
if [ "$1" = "-f" ]; then force=1; shift; fi

[ -f "$verify_diff" ] || { echo "verify_diff.py が見つかりません: $verify_diff" >&2; exit 1; }
[ -f "$template" ] || { echo "pre-commit テンプレートが見つかりません: $template" >&2; exit 1; }

if [ $# -gt 0 ]; then
    repos="$@"
else
    # guard-rules.json の repos を抽出（python で JSON を読む）
    PY="$(command -v python3 || command -v python)"
    repos=$("$PY" -c "import json,sys; print('\n'.join(json.load(open('$guards_dir/guard-rules.json', encoding='utf-8'))['repos']))")
    repos=$(echo "$repos" | while read -r r; do echo "$project_root/$r"; done)
fi

for repo in $repos; do
    if [ ! -d "$repo/.git" ]; then
        echo "WARN: git リポジトリではないためスキップ: $repo" >&2
        continue
    fi
    hook="$repo/.git/hooks/pre-commit"
    if [ -f "$hook" ] && [ $force -eq 0 ] && ! grep -q "ai-dev-flow" "$hook"; then
        echo "WARN: 既存の pre-commit が存在します（ai-dev-flow 以外）: $hook" >&2
        echo "      手動でマージするか -f で上書きしてください。スキップします。" >&2
        continue
    fi
    sed "s|__VERIFY_DIFF_PATH__|$verify_diff|g" "$template" > "$hook"
    chmod +x "$hook"
    echo "導入: $hook"
done
echo "完了。動作確認: 対象リポジトリで禁止パターンを含む変更を git commit してブロックされることを確認してください。"
