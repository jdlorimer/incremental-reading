# Copyright 2017-2019 Joseph Lorimer <joseph@lorimer.me>
#
# Permission to use, copy, modify, and distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright
# notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

export PYTHONPATH=.
VERSION=`cat _version.py | grep __version__ | sed "s/.*'\(.*\)'.*/\1/"`
PROJECT_SHORT=ir
PROJECT_LONG=incremental-reading

all: test prep pack clean

test:
	pytest --cov="$(PROJECT_SHORT)" tests -v

prep:
	rm -f $(PROJECT_LONG)-v*.zip
	find . -name '*.pyc' -type f -delete
	find . -name '*~' -type f -delete
	find . -name .mypy_cache -type d -exec rm -rf {} +
	find . -name .ropeproject -type d -exec rm -rf {} +
	find . -name __pycache__ -type d -exec rm -rf {} +
	cp LICENSE "$(PROJECT_SHORT)/LICENSE.txt"

pack:
	(cd "$(PROJECT_SHORT)" && zip -r ../$(PROJECT_LONG)-v$(VERSION).zip *)
	curl https://raw.githubusercontent.com/luoliyan/anki-misc/master/convert-readme.py --output convert-readme.py
	python convert-readme.py
	rm convert-readme.py

clean:
	rm "$(PROJECT_SHORT)/LICENSE.txt"
