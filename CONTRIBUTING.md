## Dependencies

To install dependencies:
```shell
pip install -r requirements.txt
```

To update dependencies list:
```shell
pip-compile - --output-file=- < requirements.in > requirements.txt
```

## Testing
### Unit tests

To run unit tests:
```shell
make test
```

### Manual tests

#### Add local git repo as an Anki addon
Find out where Anki stores its add-on: Open Anki > Tools > Add-ons > View Files

Then create a symlink from Anki's add-on directory to your "ir" directory.

For example:
* My Anki add-on directory is `$HOME/.local/share/Anki2/addons21`.
* My local incremental reading workspace is `$HOME/workplace/incremental-reading`.
* Then to add my local workspace as an Anki add-on, I'd run
```shell
ln -s $HOME/workplace/incremental-reading/ir  $HOME/.local/share/Anki2/addons21/ir
```

#### Run Anki from terminal

Running Anki from terminal will show stdout, which is useful for debugging.

Note: create a "Test" profile so that you don't accidentally destroy your notes.

Then run Anki from terminal
```shell
/usr/local/bin/anki -p Test
```

## Publishing

Build zip file:
```shell
make
```

Then upload it to https://ankiweb.net/shared/addons/ .