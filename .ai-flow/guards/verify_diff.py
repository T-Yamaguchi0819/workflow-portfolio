#!/usr/bin/env python
"""禁止パターンLint: git diff の追加行を機械検査する（ai-dev-flow 汎用版）

プロジェクトの「絶対禁止事項」のうち正規表現で機械検出できるものを、
モデル・レビュアーの注意力に依存せず決定論的に検査する。
検査ルールは同ディレクトリの guard-rules.json に定義する（本スクリプトは
プロジェクト非依存。ルールだけを差し替えて使う）。

検査対象は「追加行（diff の + 行）＋未追跡ファイルの全行」のみ。既存コードの
違反は報告しない（今回の修正で持ち込まれたものだけを止める）。

使い方:
    python verify_diff.py                     # ルール定義の repos を検査（未コミット変更）
    python verify_diff.py --repo <path>       # 指定リポジトリのみ（複数指定可）
    python verify_diff.py --base master       # 指定refとの差分（ブランチ全体の検査）
    python verify_diff.py --cached            # ステージ済み差分のみ（pre-commit 用）
    python verify_diff.py --config <path>     # ルール定義ファイルを指定

終了コード: 0=違反なし（WARNのみ含む）／1=ERROR違反あり／3=実行エラー
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent / 'guard-rules.json'


def load_config(config_path):
    with open(config_path, encoding='utf-8') as f:
        cfg = json.load(f)
    rules = []
    for r in cfg.get('rules', []):
        flags = re.IGNORECASE if 'i' in (r.get('flags') or '') else 0
        rules.append({
            'id': r['id'],
            'severity': r.get('severity', 'ERROR'),
            'extensions': set(r['extensions']) if r.get('extensions') else None,
            'pattern': re.compile(r['pattern'], flags),
            'message': r.get('message', ''),
            'suppressed_by': set(r.get('suppressed_by') or []),
        })
    return {
        'repos': cfg.get('repos', ['.']),
        'scan_exts': set(cfg.get('scan_extensions', [])),
        'exclude_segments': set(cfg.get('exclude_segments', [])),
        'rules': rules,
    }


def run_git(repo, *args):
    res = subprocess.run(['git', '-C', str(repo)] + list(args),
                         capture_output=True, timeout=60)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode('utf-8', errors='replace').strip())
    return res.stdout.decode('utf-8', errors='replace')


def has_head(repo):
    """初回コミット前のリポジトリでは HEAD が存在しない（diff の基準を --cached に切り替える）"""
    res = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', '-q', 'HEAD'],
                         capture_output=True, timeout=60)
    return res.returncode == 0


def is_scannable(cfg, path_str):
    p = Path(path_str)
    if cfg['scan_exts'] and p.suffix.lower() not in cfg['scan_exts']:
        return False
    return not any(seg in cfg['exclude_segments'] for seg in p.parts)


def check_line(cfg, path_str, lineno, line, findings):
    ext = Path(path_str).suffix.lower()
    hit_ids = set()
    for rule in cfg['rules']:
        if rule['extensions'] is not None and ext not in rule['extensions']:
            continue
        # 上位ルールで検出済みの行を汎用ルールで二重報告しない
        if rule['suppressed_by'] & hit_ids:
            continue
        if rule['pattern'].search(line):
            hit_ids.add(rule['id'])
            findings.append({
                'file': path_str, 'line': lineno, 'severity': rule['severity'],
                'rule': rule['id'], 'message': rule['message'],
                'content': line.strip(),
            })


DIFF_FILE_RE = re.compile(r'^\+\+\+ b/(.+)$')
HUNK_RE = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@')


def scan_diff(cfg, repo, diff_args, findings):
    """git diff の追加行を検査する"""
    diff = run_git(repo, 'diff', *diff_args, '--no-color', '--unified=0',
                   '--diff-filter=ACMR')
    current_file = None
    lineno = 0
    for raw in diff.splitlines():
        m = DIFF_FILE_RE.match(raw)
        if m:
            path = m.group(1)
            current_file = path if is_scannable(cfg, path) else None
            continue
        m = HUNK_RE.match(raw)
        if m:
            lineno = int(m.group(1))
            continue
        if current_file and raw.startswith('+') and not raw.startswith('+++'):
            check_line(cfg, current_file, lineno, raw[1:], findings)
            lineno += 1


def scan_untracked(cfg, repo, findings):
    """未追跡ファイルは全行を「追加行」として検査する"""
    out = run_git(repo, 'ls-files', '--others', '--exclude-standard')
    for rel in out.splitlines():
        rel = rel.strip()
        if not rel or not is_scannable(cfg, rel):
            continue
        try:
            text = (Path(repo) / rel).read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            check_line(cfg, rel, i, line, findings)


def main():
    ap = argparse.ArgumentParser(description='禁止パターンLint（diffの追加行を検査）')
    ap.add_argument('--repo', action='append', default=[],
                    help='検査対象リポジトリ（複数指定可。省略時はルール定義の repos）')
    ap.add_argument('--base', default='HEAD',
                    help='差分の基準ref（既定 HEAD=未コミット変更。ブランチ全体は分岐元refを指定）')
    ap.add_argument('--cached', action='store_true',
                    help='ステージ済み差分のみ検査（pre-commit 用。未追跡ファイルは対象外）')
    ap.add_argument('--config', default=str(DEFAULT_CONFIG),
                    help='ルール定義ファイル（既定: 同ディレクトリの guard-rules.json）')
    args = ap.parse_args()

    try:
        cfg = load_config(args.config)
    except (OSError, ValueError, KeyError) as e:
        print(f'ERROR: ルール定義の読み込みに失敗: {args.config}: {e}', file=sys.stderr)
        return 3

    # ルール定義の repos は「project.yaml のあるプロジェクトルート」からの相対
    # （guard-rules.json は .ai-flow/guards/ に置かれる想定）
    project_root = Path(args.config).resolve().parents[2]
    repos = [Path(r) for r in args.repo] if args.repo else \
            [project_root / r for r in cfg['repos']]

    all_findings = []
    scanned = []
    for repo in repos:
        if not (repo / '.git').exists():
            if args.repo:  # 明示指定がgitリポジトリでないのはエラー
                print(f'ERROR: git リポジトリではありません: {repo}', file=sys.stderr)
                return 3
            continue
        try:
            findings = []
            # HEAD が無い（初回コミット前）場合はステージ済み差分を基準にする
            base_args = [args.base] if has_head(repo) else ['--cached']
            if args.cached:
                scan_diff(cfg, repo, ['--cached'], findings)
            else:
                scan_diff(cfg, repo, base_args, findings)
                scan_untracked(cfg, repo, findings)
            scanned.append(repo.name)
            for f in findings:
                f['repo'] = repo.name
            all_findings.extend(findings)
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as e:
            print(f'ERROR: {repo.name} の検査に失敗: {e}', file=sys.stderr)
            return 3

    if not scanned:
        print('ERROR: 検査対象のgitリポジトリが見つかりません', file=sys.stderr)
        return 3

    errors = [f for f in all_findings if f['severity'] == 'ERROR']
    warns = [f for f in all_findings if f['severity'] == 'WARN']
    for f in all_findings:
        print(f"{f['repo']}: {f['file']}:{f['line']}: [{f['severity']}] "
              f"{f['rule']}: {f['message']}")
        print(f"    + {f['content'][:200]}")

    mode = '--cached' if args.cached else f'base={args.base}'
    print(f"検査対象: {', '.join(scanned)}（{mode}）")
    print(f"結果: ERROR {len(errors)} 件 / WARN {len(warns)} 件")
    return 1 if errors else 0


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    sys.exit(main())
