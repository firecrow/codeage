#!/usr/bin/env python
import datetime, subprocess, re, os

class CodeAgeItem(object):
    def __init__(self, filepath, relative_date, view=None):
        self.filepath = filepath
        self.relative_date = relative_date
        self.view = view
        self.relative_days = []
        self._gather_data()
        if view:
            self.view.proc_value(self.relative_days, self.relative_date)

    def _gather_data(self): 
        handle = subprocess.Popen(['git', 'blame', self.filepath], stdout=subprocess.PIPE)
        lines = handle.stdout.read().split('\n')
        extracted = []
        for l in lines:
            me = re.search('(\d{4}-\d{2}-\d{2})', l)
            if me:
                extracted.append(me.group(0))

        self.relative_days = [
                (self.relative_date - datetime.datetime.strptime(x, '%Y-%m-%d')).days 
                    for x in extracted]

class CodeAgeDir(CodeAgeItem):
    def _gather_data(self): 
        def walk(_, dir, files):
            for f in files:
                if os.path.isdir(dir+'/'+f):
                    continue
                item = CodeAgeItem(dir+'/'+f, self.relative_date)
                self.relative_days.extend(item.relative_days)

        os.path.walk(self.filepath, walk, None)


class AgeView(object):
    def __init__(self):
        self.values = ''

    def proc_value(self, relative_days, relative_date):
        total_days = sum(relative_days)
        total_count = len(relative_days)

        avg_days = total_days / total_count 
        avg_age = relative_date - datetime.timedelta(days=avg_days) 
        self.values = {
            'total_count': total_count,
            'total_days': total_days,
            'avg_days': avg_days,
            'avg_age':  avg_age,
        }

    def render_values(self):
        return str(self.values['avg_age'])

def show_results(results):
    max_width = len('filepath') 
    for v in results:
        if len(v.filepath) > max_width:
            max_width = len(v.filepath)
    max_width += 3

    print "filepath"+(max_width-len('filepath'))*' '+'value'
    results = sorted(results, key=lambda x: x.view.values['avg_days'])
    for v in results:
        print v.filepath+((max_width-len(v.filepath))*'-')+str(v.view.render_values())

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
            if os.path.exists(f):
                if os.path.isdir(f):
                    if f[-1] != '/':
                        f += '/'
                    item = CodeAgeDir(f, now, AgeView())
                    results.append(item)
                else:
                    item = CodeAgeItem(f, now, AgeView())
                    results.append(item)
            else:
                print "file not found %s" % f

    show_results(results)

