all: README.html ankiweb

ankiweb: README.ankiweb vsa-and-ire-to-ankiweb.zip

vsa-and-ire-to-ankiweb.zip: clean
	mkdir dist
	cp *.py dist/
	cd dist && zip -r ../vsa-and-ire-to-ankiweb.zip *

README.html: README.md
	markdown README.md>README.html

README.ankiweb: README.md
	markdown README.md|sed -e "s+<p>++"|sed -e "s+</p>++"| sed -e "s+<h[0-9]>+<b>+" | sed -e  "s+</h[0-9]>+</b>+">README.ankiweb


clean:
	rm -f vsa-and-ire-to-ankiweb.zip
	rm -rf dist
	rm -f README.ankiweb
	rm -f README.html

