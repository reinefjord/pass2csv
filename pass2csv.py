#!/usr/bin/env python
import csv
import os
import sys
import gnupg
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set to True to allow for alternate password csv to be created
# See README for differences
KPX_FORMAT=True

if KPX_FORMAT:
    # A list of possible fields (in order) that could be converted to login fields
    LOGIN_FIELDS=['login', 'user', 'username', 'email']
    # Set to True to extract url fields
    GET_URL=True
    # A regular expression list of lines that should be excluded from the notes field
    EXCLUDE_ROWS=['^---$', '^autotype ?: ?']

logger.info("Using KPX format: %s", KPX_FORMAT)

def traverse(path):
    for root, dirs, files in os.walk(path):
        if '.git' in dirs:
            dirs.remove('.git')
        for name in files:
            yield os.path.join(root, name)

def getMetadata(notes_raw):
    lines = notes_raw.split('\n')

    # A list of lines to keep as notes (will be joined by newline)
    notes = []
    # The extracted user field
    user = ''
    # The extracted URL field
    url = ''

    # This will extract each field name (for example, if a line in notes was `user: user1`, fields should contain 'user')
    all_fields = set()
    for line in lines:
        field_search = re.search('^(.*) ?: ?.*$', line, re.I)
        if field_search:
            all_fields.add(field_search.group(1))

    # Check if any of the fields match the login names
    login_fields = [field for field in LOGIN_FIELDS if field in all_fields]
    # Get the field to use for the login. Since LOGIN_FIELDS is in order, the 0th element will contain the first match
    login_field = None if not login_fields else login_fields[0]

    # Iterate through the file again to build the return array
    for line in lines:

        # If any of the exclusion patterns match, ignore the line
        if len([pattern for pattern in EXCLUDE_ROWS if re.search(pattern, line, re.I)]) != 0:
            continue

        if login_field:
            user_search = re.search('^' + login_field + ' ?: ?(.*)$', line, re.I)
            if user_search:
                user = user_search.group(1)
                # The user was matched, don't add it to notes
                continue

        if GET_URL:
            url_search = re.search('^url ?: ?(.*)$', line, re.I)
            if url_search:
                url = url_search.group(1)
                # The url was matched, don't add it to notes
                continue

        notes.append(line)

    return (user, url, '\n'.join(notes).strip())

def parse(basepath, path, data):
    name = os.path.splitext(os.path.basename(path))[0]
    group = os.path.dirname(os.path.os.path.relpath(path, basepath))
    split_data = data.split('\n', maxsplit=1)
    password = split_data[0]
    # Perform if/else in case there are no notes for a field
    notes = split_data[1] if len(split_data) > 1 else ""
    logger.info("Processing %s" % (name,))
    if KPX_FORMAT:
        # We are using the advanced format; try extracting user and url
        user, url, notes = getMetadata(notes)
        return [group, name, user, password, url, notes]
    else:
        # We are not using KPX format; just use notes
        return [group, name, password, notes]


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
