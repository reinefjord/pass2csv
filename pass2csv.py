#!/usr/bin/env python3
import argparse
import csv
import pathlib
import re
import sys

import gnupg

__version__ = '1.1.1'


def stderr(s, *args, **kwargs):
    print(s, *args, file=sys.stderr, **kwargs)


def set_meta(entry, path, grouping_base):
    pure_path = pathlib.PurePath(path)
    group = pure_path.relative_to(grouping_base).parent
    if group.name == '':
        group = ''
    entry['group'] = group
    entry['title'] = pure_path.stem


def set_data(entry, data, exclude, get_fields, get_lines):
    lines = data.splitlines()
    tail = lines[1:]
    entry['password'] = lines[0]

    filtered_tail = []
    for line in tail:
        for exclude_pattern in exclude:
            if exclude_pattern.search(line):
                break
        else:
            filtered_tail.append(line)

    matching_indices = set()
    fields = entry.setdefault('fields', {})

    for i, line in enumerate(filtered_tail):
        for name, pattern in get_fields:
            if name in fields:
                # multiple patterns with same name, we've already found a match
                continue
            match = pattern.search(line)
            if not match:
                continue
            inverse_match = line[0:match.start()] + line[match.end():]
            value = inverse_match.strip()
            fields[name] = value
            matching_indices.add(i)
            break

    matching_lines = {}
    for i, line in enumerate(filtered_tail):
        for name, pattern in get_lines:
            match = pattern.search(line)
            if not match:
                continue
            matches = matching_lines.setdefault(name, [])
            matches.append(line)
            matching_indices.add(i)
            break
    for name, matches in matching_lines.items():
        fields[name] = '\n'.join(matches)

    final_tail = []
    for i, line in enumerate(filtered_tail):
        if i not in matching_indices:
            final_tail.append(line)

    entry['notes'] = '\n'.join(final_tail).strip()


def write(file, entries, get_fields, get_lines, static):
    get_field_names = set(x[0] for x in get_fields)
    get_line_names = set(x[0] for x in get_lines)
    field_names = get_field_names | get_line_names
    static_names = [x[0] for x in static]
    static_values = [x[1] for x in static]
    header = ["Group(/)", "Title", "Password", *field_names, *static_names, "Notes"]
    csvw = csv.writer(file, dialect='unix')
    stderr(f"\nWriting data to {file.name}\n")
    csvw.writerow(header)
    for entry in entries:
        fields = [entry['fields'].get(name) for name in field_names]
        columns = [
            entry['group'], entry['title'], entry['password'],
            *fields,
            *static_values,
            entry['notes']
        ]
        csvw.writerow(columns)


def main(store_path, outfile, grouping_base, gpgbinary, use_agent, encodings,
         exclude, get_fields, get_lines, static):
    entries = []
    failures = []
    path = pathlib.Path(store_path)
    grouping_path = pathlib.Path(grouping_base)
    gpg = gnupg.GPG(gpgbinary=gpgbinary, use_agent=use_agent)
    files = path.glob('**/*.gpg')
    if not path.is_dir():
        if path.is_file():
            files = [path]
        else:
            stderr(f"No such file or directory: {path}")
            sys.exit(1)
    for file in files:
        stderr(f"Processing {file}")
        with open(file, 'rb') as fp:
            decrypted = gpg.decrypt_file(fp)
        if not decrypted.ok:
            err = f"Could not decrypt {file}: {decrypted.status}"
            stderr(err)
            failures.append(err)
            continue
        for i, encoding in enumerate(encodings):
            try:
                # decrypted.data is bytes
                decrypted_data = decrypted.data.decode(encoding)
            except Exception as e:
                stderr(f"Could not decode {file} with encoding {encoding}: {e}")
                continue
            if i > 0:
                # don't log if the first encoding worked
                stderr(f"Decoded {file} with encoding {encoding}")
            break
        else:
            err = "Could not decode {}, see messages above for more info.".format(file)
            failures.append(err)
            continue
        entry = {}
        set_meta(entry, file, grouping_path)
        set_data(entry, decrypted_data, exclude, get_fields, get_lines)
        entries.append(entry)
    if failures:
        stderr("\nGot errors while processing files:")
        for err in failures:
            stderr(err)
    if not entries:
        stderr("\nNothing to write.")
        sys.exit(1)
    write(outfile, entries, get_fields, get_lines, static)


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'store_path',
        metavar='STOREPATH',
        type=str,
        help="path to the password-store to export",
    )

    parser.add_argument(
        'outfile',
        metavar='OUTFILE',
        type=argparse.FileType('w'),
        help="file to write exported data to, use - for stdout",
    )

    parser.add_argument(
        '-b', '--base',
        metavar='path',
        type=str,
        help="path to use as base for grouping passwords",
        dest='base_path'
    )

    parser.add_argument(
        '-g', '--gpg',
        metavar='executable',
        type=str,
        default="gpg",
        help="path to the gpg binary you wish to use (default: '%(default)s')",
        dest='gpgbinary'
    )

    parser.add_argument(
        '-a', '--use-agent',
        action='store_true',
        default=False,
        help="ask gpg to use its auth agent",
        dest='use_agent'
    )

    parser.add_argument(
        '--encodings',
        metavar='encodings',
        type=str,
        default="utf-8",
        help=(
            "comma-separated text encodings to try, in order, when decoding"
            " gpg output (default: '%(default)s')"
        ),
        dest='encodings'
    )

    parser.add_argument(
        '-e', '--exclude',
        metavar='pattern',
        action='append',
        type=str,
        default=[],
        help=(
            "regexp for lines which should not be exported, can be specified"
            " multiple times"
        ),
        dest='exclude'
    )

    parser.add_argument(
        '-f', '--get-field',
        metavar=('name', 'pattern'),
        action='append',
        nargs=2,
        type=str,
        default=[],
        help=(
            "a name and a regexp, the part of the line matching the regexp"
            " will be removed and the remaining line will be added to a field"
            " with the chosen name. only one match per password, matching"
            " stops after the first match"
        ),
        dest='get_fields'
    )

    parser.add_argument(
        '-l', '--get-line',
        metavar=('name', 'pattern'),
        action='append',
        nargs=2,
        type=str,
        default=[],
        help=(
            "a name and a regexp for which all lines that match are included"
            " in a field with the chosen name"
        ),
        dest='get_lines'
    )

    parser.add_argument(
        '-s', '--static',
        metavar=('name', 'value'),
        action='append',
        nargs=2,
        type=str,
        default=[],
        help=("a name and a value which will be the same for all passwords"),
        dest='static'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ' + __version__
    )

    return parser.parse_args(args)


def compile_regexp(pattern):
    try:
        regexp = re.compile(pattern, re.I)
    except re.error as e:
        escaped = pattern.replace("'", "\\'")
        stderr(f"Could not compile pattern '{escaped}', {e.msg} at position {e.pos}")
        return None
    return regexp


def cli():
    parsed = parse_args()

    failed = False
    exclude_patterns = []
    for pattern in parsed.exclude:
        regexp = compile_regexp(pattern)
        if not regexp:
            failed = True
        exclude_patterns.append(regexp)

    get_fields = []
    for name, pattern in parsed.get_fields:
        regexp = compile_regexp(pattern)
        if not regexp:
            failed = True
        get_fields.append((name, regexp))

    get_lines = []
    for name, pattern in parsed.get_lines:
        regexp = compile_regexp(pattern)
        if not regexp:
            failed = True
        get_lines.append((name, regexp))

    if failed:
        sys.exit(1)

    if parsed.base_path:
        grouping_base = parsed.base_path
    else:
        grouping_base = parsed.store_path

    encodings = [e for e in parsed.encodings.split(',') if e]
    if not encodings:
        stderr(f"Did not understand '--encodings {parsed.encoding}'")
        sys.exit(1)

    kwargs = {
        'store_path': parsed.store_path,
        'outfile': parsed.outfile,
        'grouping_base': grouping_base,
        'gpgbinary': parsed.gpgbinary,
        'use_agent': parsed.use_agent,
        'encodings': encodings,
        'exclude': exclude_patterns,
        'get_fields': get_fields,
        'get_lines': get_lines,
        'static': parsed.static
    }

    main(**kwargs)

if __name__ == '__main__':
    cli()
