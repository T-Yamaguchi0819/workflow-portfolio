#!/usr/bin/env python
"""PreToolUse フック: ai-dev-flow 汎用ガード（Claude Code アダプタ）

1. git commit / git push を確認（ask）にする。
   ai-dev-flow 運用では、コミット/push の可否は project.yaml の
   git.commit_policy に従う（manual: ユーザー明示指示時のみ → ask／
   auto: フェーズ完了ごとに自動コミット・push、最終承認は PR マージ → ask しない）。
   settings.local.json の広い allow を上書きするため permission ルールでは
   なくフックで実装。`git -C <path> commit` 形式も捕捉する。
   commit_policy が読めない場合は manual 扱い（フェイルセーフ）。

2. git commit 時に禁止パターンLint（.ai-flow/guards/verify_diff.py）を自動実行し、
   ERROR 違反があればコミットをブロックする。
   Lint 自体の実行失敗時はブロックせず 1. の確認（ask）にフォールバックする。
   ※最終防壁は git pre-commit フック側。ここは早期検知層（Claude への即時フィード
     バックにより、コミット試行前に違反を直させる）。

3. プロジェクト固有のブロックが必要な場合は末尾の「拡張ポイント」に追記する
   （例: 特定ライブラリでのファイル保存禁止・特定コマンドの禁止）。

ブロック時: exit 2 ＋ stderr にメッセージ（Claude に代替手段が伝わる）
確認時:   stdout に permissionDecision=ask の JSON を出力
それ以外: exit 0（何もしない）。フック自体の異常時も exit 0（セッションを壊さない）
"""
import json
import re
import subprocess
import sys
from pathlib import Path

# .claude/hooks/ からプロジェクトルートの .ai-flow/ を参照
AI_FLOW_DIR = Path(__file__).resolve().parents[2] / '.ai-flow'
VERIFY_DIFF_SCRIPT = AI_FLOW_DIR / 'guards' / 'verify_diff.py'
PROJECT_YAML = AI_FLOW_DIR / 'project.yaml'

# git commit / push（-C <path> や git.exe 形式も捕捉）
GIT_COMMIT_PUSH_RE = re.compile(
    r'\bgit(\.exe)?\s+(-C\s+\S+\s+)?(commit|push)\b', re.IGNORECASE)
# -C のパス（引用符付きも捕捉。Lint対象リポジトリの特定用）
GIT_C_PATH_RE = re.compile(r'-C\s+(?:"([^"]+)"|\'([^\']+)\'|(\S+))')

ASK_REASON = (
    'ai-dev-flow 運用: コミット/push はユーザーが明示的に指示した場合のみ実行する'
    '（.ai-flow/project.yaml の git.commit_policy 参照）。'
    'ユーザーの指示に基づく操作であれば許可してください。'
)

LINT_BLOCK_HEADER = (
    'BLOCKED: 禁止パターンLint（.ai-flow/guards/verify_diff.py）で ERROR 違反を検出しました。'
    '違反を解消してから再度コミットしてください。'
    'ルール上許容されるべき誤検知と考える場合は、独断で回避せずユーザーに確認してください。\n\n'
)


def commit_policy_is_auto():
    """project.yaml の git.commit_policy が auto かを判定する。

    yaml パーサに依存しないよう正規表現で読む（commit_policy はファイル内で一意）。
    読めない・auto 以外の値 → False（manual 扱いのフェイルセーフ）。
    """
    try:
        text = PROJECT_YAML.read_text(encoding='utf-8')
    except Exception:
        return False
    m = re.search(r'^\s*commit_policy:\s*["\']?(\w+)["\']?', text, re.MULTILINE)
    return bool(m) and m.group(1).lower() == 'auto'


def lint_findings_for_commit(command, cwd):
    """git commit 前に verify_diff.py を実行し、ERROR 違反時に報告文字列を返す。

    Lint 自体が実行できない・失敗した場合は None（＝ブロックせず ask にフォールバック）。
    """
    if not VERIFY_DIFF_SCRIPT.exists():
        return None
    args = [sys.executable, str(VERIFY_DIFF_SCRIPT)]
    m = GIT_C_PATH_RE.search(command)
    repo = next((g for g in m.groups() if g), None) if m else None
    if repo is None and cwd and (Path(cwd) / '.git').exists():
        repo = cwd
    if repo is not None:
        args += ['--repo', str(repo)]
    # repo 特定不可 → verify_diff がルール定義（guard-rules.json の repos）で一括検査
    try:
        res = subprocess.run(args, capture_output=True, timeout=90)
    except Exception:
        return None
    if res.returncode == 1:
        return res.stdout.decode('utf-8', errors='replace')
    return None  # 0=違反なし／3=実行エラー（フェイルオープン）


def gather_text(tool_name, tool_input):
    texts = []
    if tool_name in ('Bash', 'PowerShell'):
        texts.append(tool_input.get('command') or '')
    elif tool_name == 'Write':
        texts.append(tool_input.get('content') or '')
    elif tool_name == 'Edit':
        texts.append(tool_input.get('new_string') or '')
    elif tool_name == 'MultiEdit':
        for e in tool_input.get('edits') or []:
            texts.append(e.get('new_string') or '')
    return '\n'.join(texts)


def project_specific_block(tool_name, tool_input, text):
    """拡張ポイント: プロジェクト固有のブロックルールをここに実装する。

    ブロックする場合は stderr 向けメッセージ（str）を返す。問題なければ None。
    例（openpyxl での Excel 保存を禁止する場合）:
        if re.search(r'openpyxl|load_workbook', text) and re.search(r'\\.save\\s*\\(', text):
            return 'BLOCKED: openpyxl による Excel 保存は禁止です（代替手段: ...）'
    """
    return None


def main():
    try:
        # utf-8-sig: PowerShell 経由のパイプで BOM が付くことがあるため
        raw = sys.stdin.buffer.read().decode('utf-8-sig', errors='replace')
        payload = json.loads(raw)
    except Exception:
        return 0
    tool_name = payload.get('tool_name') or ''
    tool_input = payload.get('tool_input') or {}
    text = gather_text(tool_name, tool_input)
    if not text:
        return 0

    block_msg = project_specific_block(tool_name, tool_input, text)
    if block_msg:
        sys.stderr.write(block_msg)
        return 2

    git_match = GIT_COMMIT_PUSH_RE.search(text) \
        if tool_name in ('Bash', 'PowerShell') else None
    if git_match:
        if git_match.group(3).lower() == 'commit':
            findings = lint_findings_for_commit(text, payload.get('cwd'))
            if findings:
                sys.stderr.write(LINT_BLOCK_HEADER + findings)
                return 2
        if commit_policy_is_auto():
            return 0  # auto: ask しない（Lint は上で実施済み。最終承認は PR マージ）
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'ask',
                'permissionDecisionReason': ASK_REASON,
            }
        }, ensure_ascii=False))
        return 0

    return 0


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # フック自体の異常でセッションを止めない
