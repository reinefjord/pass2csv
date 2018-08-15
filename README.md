# pass2csv
Needs [python-gnupg](https://pypi.python.org/pypi/python-gnupg) and python3.
Run with path to password store as argument:

```
python3 -m pip install --user python-gnupg
python3 pass2csv.py ~/.password-store
```

There are two ways to export CSV data:

1.  The format for the KeePass Generic CSV Importer:

        Group(/),Title,Password,Notes

    Where 'Password' is the first line of the entry in `pass` and 'Notes' are all
    subsequent lines. '\\' should not be interpreted as an escape character.

    To enable, set `KPX_FORMAT=False` in `pass2csv.py`

2.  The format for the KeePassXC Importer:

        Group(/),Title,Login,Password,URL,Notes

    Where 'Password' is the first line of the entry in `pass`, 'User' is configured
    with `LOGIN_FIELDS`, URL is extracted if `GET_URL` is set, and 'Notes' contains
    any other fields that do not match `EXCLUDE_ROWS`.

    To enable, set `KPX_FORMAT=True` and configure the variables mentioned above in
    `pass2csv.py`.

    'User' field is chosen by searching for the first field with a name in
    LOGIN_FIELDS. Once the field is found, the login is set and the field is
    removed from notes.

### Example KeePassXC Import
- Variable definitions (`pass2csv.py`)

        KPX_FORMAT=True

        LOGIN_FIELDS=['username', 'login', 'email']
        GET_URL=True
        EXCLUDE_ROWS=['^---$']

- Password entry (`sites/example`)

        password123
        ---
        username: user_name
        email: user@example.com
        url: example.com
        some_note

- Output CSV row (formatted)

        sites, example, user_name, password123, example.com, "email: user@example.com\nsome_note"

- `user_name` was chosen because `username` was the first filled entry in
  `LOGIN_FIELDS`.
- Both logn and URL fields were excluded from the notes field because they were used
in another field.
- `---` Was not included in the notes field because it was matched in `EXCLUDE_ROWS`.

### Example KeePass Generic CSV Importer
- Variable definitions (`pass2csv.py`)

        KPX_FORMAT=False

- Password entry: Same as above
- Output CSV row (formatted)

        sites, example, password123, "---\nusername: user_name\nemail: user@example.com\nurl: example.com\nsome_note"
