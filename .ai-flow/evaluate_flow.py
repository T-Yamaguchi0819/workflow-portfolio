#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""フロー評価レポート: 全タスクの 実績.md（metrics ブロック）を集計し、KPI を判定する。

使い方:
    python .ai-flow/evaluate_flow.py [-o report.md] [--json] [--yaml <project.yaml>]

- 収集対象: `{flow.work_dir}/*/No*/実績.md` の先頭 ```yaml ブロック（templates/実績.md 参照）
- 判定基準: project.yaml の `evaluation.targets`（未定義の項目は判定なしで実績のみ表示）
- 標準ライブラリのみで動く。未記入プレースホルダ（{h} 等）・null は「データなし」として除外する

exit code: 0=目標達成（または判定対象なし） / 1=未達の KPI あり / 3=実行エラー
"""
import argparse
import datetime
import glob
import io
import json
import os
import re
import sys


def fail(msg):
    sys.stderr.write(msg + '\n')
    sys.exit(3)


def read_text(path):
    with io.open(path, encoding='utf-8') as f:
        return f.read()


def yaml_scalar(v):
    v = v.strip().strip('"\'')
    if not v or v.startswith('{') or v.lower() in ('null', '~', '不明'):
        return None
    low = v.lower()
    if low in ('true', 'yes'):
        return True
    if low in ('false', 'no'):
        return False
    if re.fullmatch(r'-?\d+', v):
        return int(v)
    if re.fullmatch(r'-?\d*\.\d+', v):
        return float(v)
    return v


def parse_metrics_block(text):
    m = re.search(r'```yaml\s*\n(.*?)```', text, re.S)
    if not m:
        return None
    d = {}
    for line in m.group(1).splitlines():
        line = line.split('#', 1)[0].rstrip()
        if not line.strip() or ':' not in line:
            continue
        k, v = line.split(':', 1)
        d[k.strip()] = yaml_scalar(v)
    return d


def project_settings(yaml_text):
    """project.yaml から work_dir と evaluation を読む（yaml パーサ非依存の簡易読取）。"""
    wd = '.ai-flow/work'
    m = re.search(r'^\s*work_dir:\s*["\']?([^"\'\n#]+)', yaml_text, re.M)
    if m:
        wd = m.group(1).strip()
    targets = {}
    cycle = None
    m = re.search(r'^evaluation:[ \t]*\n((?:[ \t]+\S.*\n?)*)', yaml_text, re.M)
    if m:
        block = m.group(1)
        c = re.search(r'^\s+review_cycle:\s*(\d+)', block, re.M)
        if c:
            cycle = int(c.group(1))
        for key in ('reduction_pct_min', 'first_pass_rate_min', 'human_findings_avg_max',
                    'rework_avg_max'):
            t = re.search(r'^\s+%s:\s*([\d.]+)' % key, block, re.M)
            if t:
                targets[key] = float(t.group(1))
    return wd, targets, cycle


def num(rec, key):
    v = rec.get(key)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def avg(values):
    vals = [v for v in values if v is not None]
    return (sum(vals) / len(vals)) if vals else None


def reduction_pct(rec):
    a, b = num(rec, 'human_hours_actual'), num(rec, 'human_hours_baseline')
    if a is None or b is None or b <= 0:
        return None
    return (b - a) / b * 100.0


def rate_true(records, key):
    vals = [r.get(key) for r in records if isinstance(r.get(key), bool)]
    return (sum(1 for v in vals if v) / len(vals) * 100.0) if vals else None


def fmt(v, unit=''):
    if v is None:
        return '—'
    if isinstance(v, float):
        return ('%.1f' % v) + unit
    return str(v) + unit


def kpi_rows(records, targets):
    """(名前, 実績値, 目標表示, 達成判定 True/False/None) の一覧。"""
    red = avg([reduction_pct(r) for r in records])
    fp = rate_true(records, 'first_pass')
    hf = avg([num(r, 'human_findings') for r in records])
    rw = avg([num(r, 'rework_count') for r in records])
    rows = []

    def add(name, actual, unit, tkey, higher_is_better):
        t = targets.get(tkey)
        ok = None
        if t is not None and actual is not None:
            ok = (actual >= t) if higher_is_better else (actual <= t)
        tdisp = '—' if t is None else ('%s%s%s' % ('≥' if higher_is_better else '≤', fmt(t), unit))
        rows.append((name, fmt(actual, unit), tdisp, ok))

    add('工数削減率（平均）', red, '%', 'reduction_pct_min', True)
    add('初回PASS率', fp, '%', 'first_pass_rate_min', True)
    add('人間追加指摘（平均/タスク）', hf, '件', 'human_findings_avg_max', False)
    add('手戻り回数（平均）', rw, '回', 'rework_avg_max', False)
    return rows


def breakdown(records, key):
    groups = {}
    for r in records:
        g = r.get(key) or '不明'
        groups.setdefault(str(g), []).append(r)
    lines = []
    for g in sorted(groups):
        rs = groups[g]
        lines.append('| %s | %d | %s | %s | %s |' % (
            g, len(rs), fmt(avg([reduction_pct(r) for r in rs]), '%'),
            fmt(rate_true(rs, 'first_pass'), '%'),
            fmt(avg([num(r, 'human_findings') for r in rs]), '件')))
    return lines


def build_report(records, targets, cycle, work_dir):
    records = sorted(records, key=lambda r: (str(r.get('completed') or ''), str(r.get('task') or '')))
    today = datetime.date.today().isoformat()
    lines = ['# フロー評価レポート', '',
             '- 生成日: %s ／ 対象: %d 件の実績（%s）' % (today, len(records), work_dir)]
    if cycle:
        lines.append('- 振り返りサイクル: %d タスクごと（現在 %d 件）' % (cycle, len(records)))
    lines += ['', '## KPI 判定', '',
              '| KPI | 実績 | 目標 | 判定 |', '|-----|------|------|------|']
    ng = 0
    for name, actual, tdisp, ok in kpi_rows(records, targets):
        mark = '—' if ok is None else ('✓' if ok else '✗ 未達')
        if ok is False:
            ng += 1
        lines.append('| %s | %s | %s | %s |' % (name, actual, tdisp, mark))

    lines += ['', '## 内訳（規模別）', '',
              '| 規模 | 件数 | 削減率 | 初回PASS率 | 人間指摘 |', '|------|------|--------|-----------|---------|']
    lines += breakdown(records, 'size')
    lines += ['', '## 内訳（リスク別）', '',
              '| リスク | 件数 | 削減率 | 初回PASS率 | 人間指摘 |', '|--------|------|--------|-----------|---------|']
    lines += breakdown(records, 'risk')

    if len(records) >= 6:
        recent, earlier = records[-5:], records[:-5]
        lines += ['', '## 傾向（直近5件 vs それ以前）', '',
                  '| 指標 | それ以前 | 直近5件 |', '|------|---------|--------|',
                  '| 削減率 | %s | %s |' % (fmt(avg([reduction_pct(r) for r in earlier]), '%'),
                                            fmt(avg([reduction_pct(r) for r in recent]), '%')),
                  '| 人間追加指摘 | %s | %s |' % (fmt(avg([num(r, 'human_findings') for r in earlier]), '件'),
                                                  fmt(avg([num(r, 'human_findings') for r in recent]), '件'))]

    attention = [r for r in records if (num(r, 'human_findings') or 0) > 0
                 or r.get('flow_completed') is False or (num(r, 'escalations') or 0) > 0]
    if attention:
        lines += ['', '## 要注意タスク（precedents.md への還流を確認すること）', '']
        for r in attention:
            reasons = []
            if (num(r, 'human_findings') or 0) > 0:
                reasons.append('人間指摘 %d 件' % r['human_findings'])
            if (num(r, 'escalations') or 0) > 0:
                reasons.append('エスカレーション %d 回' % r['escalations'])
            if r.get('flow_completed') is False:
                reasons.append('フロー未完遂')
            lines.append('- %s No%s（%s）: %s' % (r.get('task') or '?', r.get('no') or '?',
                                                  r.get('completed') or '日付不明', '・'.join(reasons)))
        lines += ['', '同種の失敗が3回記録されていたら guard-rules.json・フェーズ定義への昇格を検討する（knowledge/README.md のサイクル）。']

    return '\n'.join(lines) + '\n', ng


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('-o', '--output', default=None, help='レポート出力先（省略時: 標準出力）')
    ap.add_argument('--json', action='store_true', help='集計元レコードを JSON で出力する')
    ap.add_argument('--yaml', default=None, help='project.yaml のパス（既定: .ai-flow/project.yaml）')
    args = ap.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    yaml_path = args.yaml or os.path.join(root, 'project.yaml')
    try:
        yaml_text = read_text(yaml_path)
    except Exception as e:
        fail('project.yaml を読めません: %s (%s)' % (yaml_path, e))
    work_dir, targets, cycle = project_settings(yaml_text)
    if not os.path.isabs(work_dir):
        work_dir = os.path.normpath(os.path.join(root, '..', work_dir))

    records = []
    for path in sorted(glob.glob(os.path.join(work_dir, '*', 'No*', '実績.md'))):
        try:
            rec = parse_metrics_block(read_text(path))
        except Exception:
            rec = None
        if rec is None:
            continue
        # 未記入テンプレートのコピー（識別情報も数値も無い）は集計から除外する
        if all(rec.get(k) is None for k in
               ('task', 'completed', 'human_hours_actual', 'first_pass',
                'rework_count', 'human_findings')):
            continue
        rec['_path'] = os.path.relpath(path, os.path.join(root, '..'))
        records.append(rec)

    if not records:
        print('実績データがありません（%s）。[8] で 実績.md の metrics ブロックを記録すると集計されます。' % work_dir)
        return 0

    if args.json:
        out = json.dumps(records, ensure_ascii=False, indent=2, default=str)
        ng = sum(1 for _, _, _, ok in kpi_rows(records, targets) if ok is False)
    else:
        out, ng = build_report(records, targets, cycle, work_dir)

    if args.output:
        with io.open(args.output, 'w', encoding='utf-8') as f:
            f.write(out)
        print('レポートを出力しました: %s（%d 件・未達 KPI %d 件）' % (args.output, len(records), ng))
    else:
        print(out)
    return 1 if ng else 0


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    sys.exit(main())
