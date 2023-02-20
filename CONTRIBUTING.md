# Overview
The project is structured as follow:
* `ir/` contains the source code (Python + javascript)
* `tests/` contains the test code
* `docs/` contains documentation

# Dev setup

To install dependencies:
```shell
cd ir && pip install -r requirements.txt
```

Occasionally, we'll want to update the dependencies list. You don't need this in first set-up.
To upgrade the dependencies:
```shell
cd ir && pip-compile - --output-file=- < requirements.in > requirements.txt
```

# Manual Test

## Add local repo as add-on
To iterate quickly on your changes, you should add the local repo to Anki as an add-on.
The manual testing cycle then becomes: make code changes, restart Anki, and test your change.

Steps:
1. Find where Anki stores its add-on: Open Anki > Tools > Add-ons > View Files.
2. Then create a symlink from Anki's add-on directory to your "ir" directory.
    For example:
    * My Anki add-on directory is `$HOME/.local/share/Anki2/addons21`.
    * My local incremental reading workspace is `$HOME/workplace/incremental-reading`.
    * Then to add my local workspace as an Anki add-on, I'd run
    ```shell
    ln -s $HOME/workplace/incremental-reading/ir  $HOME/.local/share/Anki2/addons21/ir
    ```
3. Restart Anki.

## Run Anki

1. Create a "Test" profile to test your changes, for your own safety.
2. Then run Anki from terminal. This will show stdout, which is useful for debugging.
    ```shell
    # On Ubuntu
    /usr/local/bin/anki -p Test

    # On Mac
    /Applications/Anki.app/Contents/MacOS/anki -p Test
    ```

# Unit test

```shell
make test
```

# Publishing

Build zip file:
```shell
make
```

Then upload it to https://ankiweb.net/shared/addons/ .
