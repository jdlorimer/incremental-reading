# Overview
The project is structured as follow:
* `ir/` contains the source code (Python + javascript)
* `tests/` contains the test code
* `docs/` contains documentation

# Dev setup
We use `poetry` to manage project dependency.

First, install poetry following the instructions from https://python-poetry.org/docs/#installation .
Then, install poetry-bumpversion plugin
```
poetry self add poetry-bumpversion
```

Then, install dependencies:
```shell
make install-deps
```

Poetry will automatically create a virtual environment and install the dependencies.
To use the virtual environment, see https://python-poetry.org/docs/basic-usage/#using-your-virtual-environment

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

1. Update the version
    ```
    poetry version patch|minor|major
    nano ir/manifest.json
    ```
2. Build the `incremental-reading-v{version}.zip` file:
    ```shell
    make
    ```
3. Test the zip file in Anki
    * Disable current IR add-on: Open Anki > Tools > Add-ons > Select current IR add-on > Toggle Enabled.
    * Add the zipped add-on: In Add-ons page > Install from file... > Pick the zip file from earlier.
    * Restart Anki to test.
    * After finish, revert the above steps.
4. Upload to https://ankiweb.net/shared/addons/ .
