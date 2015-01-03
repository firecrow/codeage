#!/usr/bin/env python
import datetime, subprocess, re

def get_datetime_avg(filepath, relative_date):
    handle = subprocess.Popen(['git', 'blame', filepath], stdout=subprocess.PIPE)
    lines = handle.stdout.read().split('\n')
    extracted = []
    for l in lines:
        me = re.search('(\d{4}-\d{2}-\d{2})', l)
        if me:
            extracted.append(me.group(0))

    relatives = [
            (relative_date - datetime.datetime.strptime(x, '%Y-%m-%d')).days 
                for x in extracted]

    avg_days = sum(relatives) / len(relatives)
    avg_age = relative_date - datetime.timedelta(days=avg_days) 
    return avg_age


def show_results(results):
    max_width = len('filepath') 
    for k,v in results:
        if len(k) > max_width:
            max_width = len(k)
    max_width += 3

    print "filepath"+(max_width-len('filepath'))*' '+'value'
    results = sorted(results, key=lambda x: x[1], reverse=True)
    for k,v in results:
        print k+((max_width-len(k))*'-')+str(v)

if __name__ == '__main__':
    import argparse

    def process_args():
        parser = argparse.ArgumentParser(
            description="Bucket lines or percentage of file in git blame\nto show code age average or number since a given date")

        parser.add_argument('--after','-t', type=str, nargs='?',
            help="date (e.g. 2012-01-21) show only counts for lines altered after this date")

        parser.add_argument('--depth','-d', type=int, nargs='?',
            help="n aggregate values to the n folder level")

        parser.add_argument('--files','-f', nargs='+',
            help="files and directories to gather data from")

        parser.add_argument('--lines','-l', action='store_true',
            help="show line numbers, meaingless without --after")
        parser.add_argument('--average','-a', type=bool,
            help="show the average date for the file if --files or files in folder if --folders (DEFAULT)")

        args_obj = parser.parse_args()
        # lack of dict comprehensions in python 2.6
        _args = {}
        for k,v in args_obj._get_kwargs():
            _args[k] = v

        # set defaults
        if _args['depth']:
            _args['type'] = 'folder'
        else:
            _args['type'] = 'files'

        if not _args['lines']:
            _args['average'] = True
        return _args

    args = process_args()
        
    now = datetime.datetime.now()
    results = []
    if args['type'] == 'files':
        for f in args['files']:
            avg = get_datetime_avg(f, now)
            results.append((f,avg))

    show_results(results)

