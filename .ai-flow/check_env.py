#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""導入前提チェック: フローの各機能に必要なツール・ライブラリの過不足を表示する。

使い方:
    python .ai-flow/check_env.py

- project.yaml の設定（issue_sync.enabled・git.commit_policy・docs.enabled）を読み、
  **このプロジェクトの構成で**必須かどうかを判定して表示する
- 導入の最初と、project.yaml で機能を有効化した後に実行する（docs/導入ガイド.md 参照）
- 標準ライブラリのみで動く（このスクリプト自体に追加ライブラリは不要）

exit code: 0=必須がすべて揃っている / 1=必須に不足あり
"""
import argparse
import importlib.util
import re
import shutil
import sys
from pathlib import Path


def load_yaml_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception:
        return ''


def block_enabled(yaml_text, block):
    """`block:` 直下のインデント行から `enabled: true` を探す（yaml パーサ非依存）。"""
    m = re.search(r'^%s:[ \t]*\n((?:[ \t]+\S.*\n?)*)' % re.escape(block), yaml_text, re.M)
    if not m:
        return False
    return re.search(r'^[ \t]+enabled:[ \t]*true\b', m.group(1), re.M) is not None


def has_cmd(name):
    return shutil.which(name) is not None


def has_mod(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--yaml', default=None, help='project.yaml のパス（既定: このスクリプトと同じ .ai-flow/ 内）')
    args = ap.parse_args()

    yaml_path = args.yaml or str(Path(__file__).resolve().parent / 'project.yaml')
    text = load_yaml_text(yaml_path)
    if not text:
        print('WARN: project.yaml を読めません（%s）。全機能を「任意」として判定します。' % yaml_path)

    issue_on = block_enabled(text, 'issue_sync')
    docs_on = block_enabled(text, 'docs')
    auto = bool(re.search(r'^\s*commit_policy:\s*["\']?auto\b', text, re.M))

    # (名前, 充足しているか, レベル, 必要になる機能, 導入方法)
    rows = [
        ('Python 3.8+', sys.version_info >= (3, 8), '必須',
         'guards（禁止パターンLint）・各スクリプトの実行', 'https://www.python.org/'),
        ('git', has_cmd('git'), '必須',
         'ブランチ運用・pre-commit フック', '-'),
        ('gh CLI', has_cmd('gh'), '必須' if (issue_on or auto) else '任意',
         'Issue ミラー（issue_sync）・PR 発行/レビュー（commit_policy: auto）',
         'https://cli.github.com/ → 導入後に gh auth login'),
        ('openpyxl', has_mod('openpyxl'), '推奨' if docs_on else '任意',
         'Excel 書式テンプレート（抽出/検査。docs.targets[].style）', 'pip install openpyxl pyyaml'),
        ('PyYAML', has_mod('yaml'), '推奨' if docs_on else '任意',
         'Excel 書式テンプレート（抽出/検査。docs.targets[].style）', 'pip install openpyxl pyyaml'),
        ('pywin32', has_mod('win32com'), '任意',
         'Excel COM 書き込み（docs.excel_write_policy。Windows のみ）', 'pip install pywin32'),
    ]

    print('ai-dev-flow 導入前提チェック（project.yaml: issue_sync=%s / commit_policy=%s / docs=%s）'
          % ('on' if issue_on else 'off', 'auto' if auto else 'manual', 'on' if docs_on else 'off'))
    print()
    print('  %-2s %-14s %-4s %-52s %s' % ('', 'ツール', 'レベル', '必要になる機能', '導入方法'))
    missing_required = []
    for name, ok, level, reason, install in rows:
        mark = '✓' if ok else ('✗' if level == '必須' else '−')
        print('  %-2s %-14s %-4s %-52s %s' % (mark, name, level, reason, '-' if ok else install))
        if not ok and level == '必須':
            missing_required.append(name)
    print()
    if missing_required:
        print('NG: 必須が不足しています → %s' % '、'.join(missing_required))
        print('    導入後に本スクリプトを再実行してください。')
        return 1
    recommend = [r[0] for r in rows if not r[1] and r[2] == '推奨']
    if recommend:
        print('OK: 必須は揃っています（推奨の未導入: %s。該当機能を使う時点で必要になります）'
              % '、'.join(recommend))
    else:
        print('OK: 必須は揃っています。')
    return 0


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    sys.exit(main())
