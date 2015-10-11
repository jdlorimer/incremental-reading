all: vsa-and-ire-to-ankiweb.zip

vsa-and-ire-to-ankiweb.zip: clean README.html
	mkdir dist
	cp *.py dist/
	cd dist && zip -r ../vsa-and-ire-to-ankiweb.zip *

README.html: README.md
	markdown README.md>README.html

clean:
	rm -f vsa-and-ire-to-ankiweb.zip
	rm -rf dist
