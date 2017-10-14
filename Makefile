VERSION = `cat _version.py | grep __version__ | sed "s/.*'\(.*\)'.*/\1/"`

all: prep pack clean

prep:
	rm -f incremental-reading-v*.zip
	find . -name .ropeproject -type d -exec rm -rf {} +
	find . -name __pycache__ -type d -exec rm -rf {} +
	find . -name "*.pyc" -type f -delete
	find . -name "*~" -type f -delete
	mv ir/meta.json .
	cp LICENSE-ISC ir/LICENSE.txt

pack:
	cd ir && zip -r ../incremental-reading-v$(VERSION).zip *

clean:
	rm ir/LICENSE.txt
	mv meta.json ir/meta.json
