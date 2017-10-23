import csv
import os
import sys
import gnupg


def traverse(path):
    for root, dirs, files in os.walk(path):
        if '.git' in dirs:
            dirs.remove('.git')
        for name in files:
            yield os.path.join(root, name)


def parse(basepath, path, data):
    title = os.path.splitext(os.path.basename(path))[0]
    group = os.path.dirname(os.path.os.path.relpath(path, basepath))
    split_data = data.split('\n', maxsplit=1)
    password = split_data[0]
    notes = split_data[1]
    username = ''
    url = ''
    note_lines = notes.split('\n')
    notes = ''
    for line in note_lines:
        if line[:6]=='login:':
            username = line[7:]
        elif line[:4]=='url:':
            url = line[5:]
        else:
            notes += line+'\n'
    return [group, title, username, password, url, notes]


def main(path):
    gpg = gnupg.GPG()
    gpg.encoding = 'utf-8'
    csv_data = []
    for file_path in traverse(path):
        if os.path.splitext(file_path)[1] == '.gpg':
            with open(file_path, 'rb') as f:
                data = str(gpg.decrypt_file(f))
                csv_data.append(parse(path, file_path, data))
    with open('pass.csv', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerows(csv_data)


if __name__ == '__main__':
    path = os.path.abspath(sys.argv[1])
    main(path)
