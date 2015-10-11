all: vsa-and-ire-to-ankiweb.zip

vsa-and-ire-to-ankiweb.zip: clean
	mkdir dist
	cp *.py dist/
	cd dist && zip -r ../vsa-and-ire-to-ankiweb.zip *

clean:
	rm -f vsa-and-ire-to-ankiweb.zip
	rm -rf dist
