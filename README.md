# pass2csv

Source is available [at GitHub](https://github.com/reinefjord/pass2csv).

Requires [python-gnupg](https://pypi.python.org/pypi/python-gnupg) and python3.
Run with path to password store as argument:

```
python3 -m pip install --user python-gnupg
python3 pass2csv.py ~/.password-store
```


## Usage

```
$ pass2csv --help
usage: pass2csv.py [-h] [-a] [-b GPGBINARY] [-x] [-l LOGIN_FIELDS [LOGIN_FIELDS ...]] [-u]
                   [-e EXCLUDE_ROWS [EXCLUDE_ROWS ...]]
                   path

positional arguments:
  path                  path to the password-store folder to export

optional arguments:
  -h, --help            show this help message and exit
  -a, --agent           ask gpg to use its auth agent
  -b GPGBINARY, --gpgbinary GPGBINARY
                        path to the gpg binary you wish to use
  -x, --kpx             format the CSV for KeePassXC
  -l LOGIN_FIELDS [LOGIN_FIELDS ...], --login-fields LOGIN_FIELDS [LOGIN_FIELDS ...]
                        strings to interpret as names of login fields (only used with -x)
  -u, --get-url         match row starting with 'url:' and extract it (only used with -x)
  -e EXCLUDE_ROWS [EXCLUDE_ROWS ...], --exclude-rows EXCLUDE_ROWS [EXCLUDE_ROWS ...]
                        regexps to exclude from the notes field (only used with -x)

```


## Export format
There are two ways to export CSV data:

1.  The format for the KeePass Generic CSV Importer:

        Group(/),Title,Password,Notes

    Where 'Password' is the first line of the entry in `pass` and
    'Notes' are all subsequent lines. '\\' should not be interpreted as
    an escape character.

    This is the default mode.

2.  The format for the KeePassXC Importer:

        Group(/),Title,Login,Password,URL,Notes

    Where 'Password' is the first line of the entry in `pass`, 'User' is
    configured with `-l`, URL is extracted if `-u` is
    set, and 'Notes' contains any other fields that do not match
    `-e`.

    'User' field is chosen by searching for the first field with a name
    set by `-l`. Once the field is found, the login is set and the field
    is removed from notes.

    Use `-x` or `--kpx` to enable this mode.


### Example KeePassXC Import
- Cmd line

        pass2csv ~/.password-store -x -l username login email -u -e '^---$'

- Password entry (`sites/example`)

        password123
        ---
        username: user_name
        email: user@example.com
        url: example.com
        some_note

- Output CSV row (formatted)

        sites, example, user_name, password123, example.com, "email: user@example.com\nsome_note"

- `user_name` was chosen because `username` was the first argument to `-l`.
- Both logn and URL fields were excluded from the notes field because they
  were used in another field.
- `---` Was not included in the notes field because it was matched by `-e`.


### Example KeePass Generic CSV Importer
- Cmd line

        pass2csv ~/.password-store

- Password entry: Same as above
- Output CSV row (formatted)

        sites, example, password123, "---\nusername: user_name\nemail: user@example.com\nurl: example.com\nsome_note"


## Development
Create a virtual environment:

```sh
python3 -m venv venv
```

Activate the environment:

```sh
. venv/bin/activate
```

Now you may either use `pip` directly to install the dependencies, or
you can install `pip-tools`. The latter is recommended.

### pip

```sh
pip install -r requirements.txt
```


### pip-tools
[pip-tools](https://github.com/jazzband/pip-tools) can keep your virtual
environment in sync with the `requirements.txt` file, as well as compiling a
new `requirements.txt` when adding/removing a dependency in `requirements.in`.

It is recommended that pip-tools is installed within the virutal
environment.

```sh
pip install pip-tools
pip-compile  # only necessary when adding/removing a dependency
pip-sync
```
