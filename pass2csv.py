#!/usr/bin/env python3
import csv
import logging
import os
import re
from argparse import ArgumentParser

import gnupg


class CSVExporter():

    def __init__(self, kpx_format):

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Set to True to allow for alternate password csv to be created
        # See README for differences
        self.kpx_format = kpx_format

        if self.kpx_format:
            # A list of possible fields (in order) that could be converted to login fields
            self.login_fields = ['login', 'user', 'username', 'email']
            # Set to True to extract url fields
            self.get_url = True
            # A regular expression list of lines that should be excluded from the notes field
            self.exclude_rows = ['^---$', '^autotype ?: ?']

        self.logger.info("Using KPX format: %s", self.kpx_format)

    def traverse(self, path):

        for root, dirs, files in os.walk(path):
            if '.git' in dirs:
                dirs.remove('.git')
            for name in files:
                yield os.path.join(root, name)

    def getMetadata(self, notes_raw):

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
        login_fields = [
            field for field in self.login_fields if field in all_fields]
        # Get the field to use for the login. Since self.login_fields is in order, the 0th element will contain the first match
        login_field = None if not login_fields else login_fields[0]

        # Iterate through the file again to build the return array
        for line in lines:

            # If any of the exclusion patterns match, ignore the line
            if [pattern for pattern in self.exclude_rows if re.search(pattern, line, re.I)]:
                continue

            if login_field:
                user_search = re.search(
                    '^' + login_field + ' ?: ?(.*)$', line, re.I)
                if user_search:
                    user = user_search.group(1)
                    # The user was matched, don't add it to notes
                    continue

            if self.get_url:
                url_search = re.search('^url ?: ?(.*)$', line, re.I)
                if url_search:
                    url = url_search.group(1)
                    # The url was matched, don't add it to notes
                    continue

            notes.append(line)

        return (user, url, '\n'.join(notes).strip())

    def parse(self, basepath, path, data):

        name = os.path.splitext(os.path.basename(path))[0]
        group = os.path.dirname(os.path.os.path.relpath(path, basepath))
        split_data = data.split('\n', maxsplit=1)
        password = split_data[0]
        # Perform if/else in case there are no notes for a field
        notes = split_data[1] if len(split_data) > 1 else ""
        self.logger.info("Processing %s", name)
        if self.kpx_format:
            # We are using the advanced format; try extracting user and url
            user, url, notes = self.getMetadata(notes)
            return [group, name, user, password, url, notes]
        else:
            # We are not using KPX format; just use notes
            return [group, name, password, notes]


def main(kpx_format, gpgbinary, use_agent, pass_path):
    """Main script entrypoint."""

    exporter = CSVExporter(kpx_format)
    gpg = gnupg.GPG(use_agent=use_agent, gpgbinary=gpgbinary)
    gpg.encoding = 'utf-8'
    csv_data = []
    for file_path in exporter.traverse(pass_path):
        if os.path.splitext(file_path)[1] == '.gpg':
            with open(file_path, 'rb') as f:
                data = str(gpg.decrypt_file(f))
                if str == "":
                    raise ValueError("The password file is empty")
                csv_data.append(exporter.parse(pass_path, file_path, data))

    with open('pass.csv', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerows(csv_data)


class OptionsParser(ArgumentParser):
    """Regular ArgumentParser with the script's options."""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.add_argument(
            '-p', '--path',
            type=str,
            help="Path to the PasswordStore folder to use",
            dest='pass_path',
        )

        self.add_argument(
            '-a', '--agent',
            action='store_true',
            help="Use this option to ask gpg to use it's auth agent",
            dest='use_agent',
        )

        self.add_argument(
            '-b', '--gpgbinary',
            type=str,
            help="Path to the gpg binary you wish to use",
            dest='gpgbinary',
            default="gpg"
        )

        self.add_argument(
            '-x', '--kpx',
            action='store_true',
            help="Use this option to format the CSV for KeePassXC",
            dest='kpx_format',
        )


if __name__ == '__main__':
    PARSER = OptionsParser()
    ARGS = PARSER.parse_args()
    main(**vars(ARGS))
