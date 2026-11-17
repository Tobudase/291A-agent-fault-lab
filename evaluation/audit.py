"""Audit frozen holdout rows and produce the descriptive statistics for the PDF."""
import argparse
import hashlib
import json
import statistics as st
from collections import Counter
from pathlib import Path

from analysis import load
from analyze_phase2_provenance import check_reuse
from reporting import final_report as release
from .holdout import SPEC, config
from mas import tasks


def summarize(rows):
    n = len(rows)
    return dict(n=n, correct=sum(r['correct'] for r in rows), safe=sum(release.completed(r) for r in rows),
                tokens=st.mean(r['total_tokens'] for r in rows), latency=st.mean(r['total_latency'] for r in rows),
                status=dict(Counter(r.get('recovery_status', 'workflow') for r in rows)),
                not_fired=sum(r.get('outcome') == 'not_fired' for r in rows))


def main(root):
    workloads = {t[0]: tasks.Task(*t) for t in SPEC['tasks']}
    tasks.CASH_MODE = 'ample'
    release.TASKS_BY_ID.update(workloads)
    keys = {(t, 'clean', m) for t in workloads for m in ('none','verify')}
    keys |= {(t,f,m) for t in workloads for f in SPEC['faults'] for m in SPEC['methods']}
    all_rows, reuse, source_ids = [], Counter(), set()
    for i in range(1, SPEC['repetitions']+1):
        directory = root / f'repeat-{i}'
        manifest = release.read(directory/'manifest.json')
        assert manifest == config(), 'auditor and runner configs differ'
        raw = [json.loads(s) for s in (directory/'results.jsonl').read_text().splitlines()]
        assert len(raw) == len(keys) and {(r['task'],r['fault'],r['method']) for r in raw} == keys
        assert len(list(directory.glob('*/*/*/trace.json'))) == len(keys)
        for r in raw:
            t,f,m = r['task'],r['fault'],r['method']
            data = release.validate_trace(directory/t/f/m/'trace.json')
            assert r == data['metrics'] and r['config'] == manifest
            if m == 'none':
                assert data['trace']['run_id'] not in source_ids
                source_ids.add(data['trace']['run_id'])
            if m in release.RECOVERY:
                source = release.read(directory/t/f/'none/trace.json')['trace']
                clean = release.read(directory/t/'clean/none/trace.json')['trace']
                assert r['source_trace_id'] == source['run_id']
                reuse[m] += check_reuse(directory,t,f,m,source,clean)[0]
        all_rows.extend(dict(row,repeat=i) for row in load(str(directory)))
    faulty = [r for r in all_rows if r['fault'] != 'clean']
    methods = {m:summarize([r for r in faulty if r['method']==m]) for m in SPEC['methods']}
    controls = {m:summarize([r for r in all_rows if r['fault']=='clean' and r['method']==m]) for m in ('none','verify')}
    by_fault = {f:{m:summarize([r for r in faulty if r['fault']==f and r['method']==m]) for m in SPEC['methods']} for f in SPEC['faults']}
    base = {(r['repeat'],r['task'],r['fault']):r for r in faulty if r['method']=='restart'}
    none = {(r['repeat'],r['task'],r['fault']):r for r in faulty if r['method']=='none'}
    paired = {}
    for m in ('restart','selective','change_aware'):
        rows = [r for r in faulty if r['method']==m]
        def key(r): return r['repeat'],r['task'],r['fault']
        def saving(subset): return 100*(1-sum(r['total_tokens'] for r in subset)/sum(base[key(r)]['total_tokens'] for r in subset))
        paired[m] = dict(saving=saving(rows), by_task={t:saving([r for r in rows if r['task']==t]) for t in workloads},
            by_repeat=[saving([r for r in rows if r['repeat']==i]) for i in range(1,4)],
            rescued=sum(release.completed(r) and not none[key(r)]['safe_success'] for r in rows),
            lower=sum(r['total_tokens']<base[key(r)]['total_tokens'] for r in rows))
    report = dict(rows=len(all_rows),reuse=dict(reuse),controls=controls,methods=methods,by_fault=by_fault,paired=paired)
    (root/'AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
    (root/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=1)+'\n')
    print('Audited',len(all_rows),'episodes across',len(base),'paired fault exposures.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('root',type=Path); main(parser.parse_args().root)
