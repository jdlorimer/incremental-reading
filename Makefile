VERSION = `cat ir/_version.py | grep __version__ | sed "s/.*'\(.*\)'.*/\1/"`

all: clean zipfile

clean:
	rm -f incremental-reading-v*.zip
	rm -rf dist
	find . -name "*~" -type f -delete
	find . -name "*.pyc" -type f -delete
	find . -name .ropeproject -type d -exec rm -rf {} +

zipfile:
	mkdir dist
	cp ir_addon.py dist
	cp -R ir dist
	cd dist && zip -r ../incremental-reading-v$(VERSION).zip *
