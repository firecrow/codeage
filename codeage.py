if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="Bucket lines or percentage of file in git blame\nto show code age average or number since a given date")

    parser.add_argument('--after','-t', type=str, nargs='?',
        help="date (e.g. 2012-01-21) show only counts for lines altered after this date")

    parser.add_argument('--depth','-d', type=int, nargs='?',
        help="n aggregate values to the n folder level")
    parser.add_argument('--files','-f', action='store_true',
        help="show numbers for all files (DEFAULT)")

    parser.add_argument('--lines','-l', action='store_true',
        help="show line numbers, meaingless without --after")
    parser.add_argument('--average','-a', type=bool,
        help="show the average date for the file if --files or files in folder if --folders (DEFAULT)")

    args_obj = parser.parse_args()
    # lack of dict comprehensions in python 2.6
    args = {}
    for k,v in args_obj._get_kwargs():
        args[k] = v

    # set defaults
    if args['depth']:
        args['type'] = 'folder'
    else:
        args['type'] = 'files'

    if not args['lines']:
        args['average'] = True
        
    print args




