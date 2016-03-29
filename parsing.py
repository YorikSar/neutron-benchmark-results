from __future__ import print_function

import collections
import itertools
import json
import os
import re


def all_results(dirname, f):
    for fname in os.listdir(dirname):
        if fname.endswith('.html'):
            yield fname, f(os.path.join(dirname, fname))


def find_first_line_match(fname, regexp, num_lines):
    with open(fname) as f:
        for line in itertools.islice(f, num_lines):
            match = re.search(regexp, line)
            if match:
                return match
        else:
            return None


def shaker_load(fname):
    match = find_first_line_match(fname, r'var report = (.*);', 100)
    if match:
        return json.loads(match.group(1))


def all_shaker_results():
    return all_results('shaker', shaker_load)


def rally_load(fname):
    match = find_first_line_match(fname, r'\$scope\.source = (.*);', 30)
    if not match:
        return None
    source_str = json.loads(match.group(1))
    source = json.loads(source_str)
    match = find_first_line_match(fname, r'\$scope\.scenarios = (.*);', 30)
    if not match:
        return None
    scenarios = json.loads(match.group(1))
    return {'source': source, 'scenarios': scenarios}


def all_rally_results():
    return all_results('rally', rally_load)


def shaker_get_max_min_stats(records):
    stats = collections.defaultdict({
        'max': None, 'min': None, 'sum': 0, 'count': 0,
    }.copy)
    for record in records.itervalues():
        if 'stats' not in record:
            continue
        for type, r_stats in record['stats'].iteritems():
            t_stats = stats[type]
            if t_stats['max'] is None or t_stats['max'] < r_stats['max']:
                t_stats['max'] = r_stats['max']
            if t_stats['min'] is None or t_stats['min'] > r_stats['min']:
                t_stats['min'] = r_stats['min']
            t_stats['sum'] += r_stats['mean']
            t_stats['count'] += 1
            t_stats['unit'] = r_stats['unit']
    for t_stats in stats.itervalues():
        t_stats['mean'] = float(t_stats['sum']) / t_stats['count']
    return dict(stats)

def main():
    print("Shaker:")
    for fname, res in all_shaker_results():
        print(
            fname,
            shaker_get_max_min_stats(res['records']),
            list(res['scenarios']),
            collections.Counter(r.get('status')
                                for r in res['records'].itervalues()),
        )
    print("Rally:")
    for fname, res in all_rally_results():
        print(
            fname,
            [[
                name,
                task[0]['runner']['concurrency'],
                task[0]['runner']['times'],
            ] for name, task in res['source'].iteritems()],
            [len(s['errors']) for s in res['scenarios']],
        )

if __name__ == '__main__':
    try:
        main()
    except Exception:
        import pdb
        pdb.post_mortem()
        raise
