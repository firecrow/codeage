#!/usr/bin/env python
import datetime, subprocess, re, os, sys

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
        handle = subprocess.Popen(['git', 'blame', self.filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        handle = subprocess.Popen(['find', self.filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lines = handle.stdout.read().split('\n')
        total_files_count = 0
        for l in lines:
            if l:
                if l[-1] == '/':
                    continue
                total_files_count += 1

        files_count = [0]
        def walk(_, dir, files):
            for f in files:
                if os.path.isdir(dir+'/'+f):
                    continue
                item = CodeAgeItem(dir+'/'+f, self.relative_date)
                self.relative_days.extend(item.relative_days)
                files_count[0] += 1
                self.view.set_status('file', {
                        'files_count':files_count[0], 
                        'total_files_count':total_files_count,
                        'filepath':self.filepath,
                    })

        os.path.walk(self.filepath, walk, None)

class View(object):
    def __init__(self, total_file_args):
        self.values = ''
        self.sort_reverse = False
        self.total_file_args = total_file_args
        self.tool = RenderTools()
        self.file_complete_count = 0
        self.current_file = None

    def set_status(self, type, data):
        if type == 'file':
            if self.current_file != data['filepath']:
                self.file_complete_count += 1
                self.current_file = data['filepath']
            pathname_length = len(data['filepath'])
            percent = int(float(data['files_count'])/data['total_files_count']*100)
            sys.stdout.write(data['filepath'] + ' ')
            sys.stdout.write(self.tool.render_spinner())
            sys.stdout.write('%s%%' % percent)
            count_str = ' %s of %s' % (self.file_complete_count, self.total_file_args)
            sys.stdout.write(' %s' % count_str)
            sys.stdout.write('\033[%sD' % (len(count_str)+1+pathname_length + 6))
            sys.stdout.flush()

    def proc_value(self, relative_days, relative_date):
        pass
    def render_values(self):
        pass 
    def get_sort_key(self):
        pass

class AgeView(View):
    def __init__(self, total_file_args):
        self.values = ''
        self.sort_reverse = True 
        self.total_file_args = total_file_args
        self.tool = RenderTools()
        self.total_file_args = total_file_args
        self.file_complete_count = 0
        self.current_file = None

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

    def get_sort_key(self):
        return self.values['avg_age']


class SinceView(View):
    def __init__(self, total_file_args):
        self.values = ''
        self.sort_reverse = True 
        self.total_file_args = total_file_args
        self.tool = RenderTools()
        self.total_file_args = total_file_args
        self.file_complete_count = 0
        self.current_file = None

    def proc_value(self, relative_days, relative_date):
        total_count = len(relative_days)
        since_count = len([x for x in relative_days if x < 0])
        self.values = {
            'total_count': total_count,
            'since_count': since_count,
        }

    def render_values(self):
        return '%s/%s' % (self.values['since_count'], self.values['total_count'])

    def get_sort_key(self):
        return float(self.values['since_count'])/self.values['total_count']*100



class RenderTools(object):
    def __init__(self):
        self.states = ['|','/','-','\\','|','/','-', '\\']
        self.state = 0

    def render_spinner(self):
        val = self.states[self.state]
        self.increment()
        return val

    def increment(self):
        if self.state > 6:
            self.state = 0
            return
        self.state += 1


class SinceViewPercent(SinceView):
    def render_values(self):
        return  str(int(float(self.values['since_count'])/self.values['total_count']*100)) + '%'


def show_results(results, args):
    max_width = len('filepath') 
    for v in results:
        if len(v.filepath) > max_width:
            max_width = len(v.filepath)
    max_width += 3

    if args['since']:
        value_column_name = 'lines since %s' % args['since']
    else:
        value_column_name = 'average age'

    print "filepath"+(max_width-len('filepath'))*' '+value_column_name
    results = sorted(results, key=lambda x: x.view.get_sort_key(), reverse=results[0].view.sort_reverse)
    for v in results:
        print v.filepath+((max_width-len(v.filepath))*'-')+str(v.view.render_values())

if __name__ == '__main__':
    import argparse

    def process_args():
        parser = argparse.ArgumentParser(
            description="Bucket lines or percentage of file in git blame\nto show code age average or number since a given date")

        parser.add_argument('--since','-s', type=str, nargs='?',
            help="date (e.g. 2012-01-21) show only counts for lines altered after this date")

        parser.add_argument('--files','-f', nargs='+',
            help="files and directories to gather data from")

        parser.add_argument('--percent','-p', action='store_true',
            help="show percentage of lines, only works with --since flag")

        args_obj = parser.parse_args()
        # lack of dict comprehensions in python 2.6
        _args = {}
        for k,v in args_obj._get_kwargs():
            _args[k] = v
        return _args

    args = process_args()
        
    results = []
    
    if args['since']:
        relative_date = datetime.datetime.strptime(args['since'], '%Y-%m-%d')
        if args['percent']:
            viewcls = SinceViewPercent
        else:
            viewcls = SinceView
    else:
        relative_date = datetime.datetime.now()
        viewcls = AgeView

    view = viewcls(len(args['files']))
    for f in args['files']:
        if os.path.exists(f):
            if os.path.isdir(f):
                if f[-1] != '/':
                    f += '/'
                item = CodeAgeDir(f, relative_date, view)
            else:
                item = CodeAgeItem(f, relative_date, view)
            if item.relative_days:
                results.append(item)
        else:
            print "file not found %s" % f

    show_results(results, args)

