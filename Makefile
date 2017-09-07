VERSION = `cat __init__.py | grep __version__ | sed "s/.*'\(.*\)'.*/\1/"`

all: clean zipfile

clean:
	rm -f incremental-reading-v*.zip
	find . -name "*~" -type f -delete
	find . -name .ropeproject -type d -exec rm -rf {} +
	find . -name __pycache__ -type d -exec rm -rf {} +

zipfile:
	cp LICENSE-ISC ir/LICENSE.txt
	cd ir && zip -r ../incremental-reading-v$(VERSION).zip *
	rm ir/LICENSE.txt
