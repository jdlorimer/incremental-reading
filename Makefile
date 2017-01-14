all: clean zipfile

clean:
	rm -f incremental-reading.zip
	rm -rf dist
	find . -name "*~" -type f -delete
	find . -name .ropeproject -type d -exec rm -rf {} +

zipfile:
	mkdir dist
	cp ir_addon.py dist
	cp -R ir dist
	cd dist && zip -r ../incremental-reading.zip *
