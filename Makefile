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
VERSION=$(shell poetry version -s)
PROJECT_SHORT=ir
PROJECT_LONG=incremental-reading

DIST_DIR=$(CURDIR)/dist
DIST_FILE_PATH=$(DIST_DIR)/$(PROJECT_LONG)-v$(VERSION).zip

all: test clean pack

install-deps:
	poetry install --sync --no-root

test:
	poetry run pytest --cov="$(PROJECT_SHORT)" tests -v

clean:
	rm -rf "$(DIST_DIR)"
	find . -name '*.pyc' -type f -delete
	find . -name '*~' -type f -delete
	find . -name .mypy_cache -type d -exec rm -rf {} +
	find . -name .ropeproject -type d -exec rm -rf {} +
	find . -name __pycache__ -type d -exec rm -rf {} +

pack:
	mkdir -p "$(DIST_DIR)"
	cd "$(PROJECT_SHORT)" && zip -r "$(DIST_FILE_PATH)" *
	zip $(DIST_FILE_PATH) LICENSE.md