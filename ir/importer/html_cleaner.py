from typing import Set, Union
from urllib.parse import urljoin, urlsplit
from urllib.request import url2pathname

from aqt import mw
from bs4 import BeautifulSoup, Comment, Tag


class HtmlCleaner:
    _BAD_TAGS: Set[str] = {"iframe", "script"}

    def clean(
        self, html: Union[bytes, str], url: str, local: bool = False
    ) -> BeautifulSoup:
        webpage = BeautifulSoup(html, "html.parser")

        for tagName in self._BAD_TAGS:
            for tag in webpage.find_all(tagName):
                tag.decompose()

        for c in webpage.find_all(text=lambda s: isinstance(s, Comment)):
            c.extract()

        for a in webpage.find_all("a"):
            self._processATag(url, a)

        for img in webpage.find_all("img"):
            self._processImgTag(url, img, local)

        for link in webpage.find_all("link"):
            self._processLinkTag(url, link, local)

        return webpage

    def _processATag(self, url: str, a: Tag) -> None:
        if a.get("href"):
            if a["href"].startswith("#"):
                # Need to override onclick for named anchor to work
                # See https://forums.ankiweb.net/t/links-to-named-anchors-malfunction/5157
                if not a.get("onclick"):
                    named_anchor = a["href"][1:]  # Remove first hash
                    a["href"] = "javascript:;"
                    a["onclick"] = f"document.location.hash='{named_anchor}';"
            else:
                a["href"] = urljoin(url, a["href"])

    def _processImgTag(self, url: str, img: Tag, local: bool = False) -> None:
        """
        Copy image from local storage to Anki media folder and replace src with local path
        """
        if not img.get("src"):
            return

        img["src"] = urljoin(url, img["src"])
        if local and urlsplit(img["src"]).scheme == "file":
            filepath = url2pathname(urlsplit(img["src"]).path)
            # TODO: remove mw reference
            mediafilepath = mw.col.media.add_file(filepath)
            img["src"] = mediafilepath

        # Some webpages send broken base64-encoded URI in srcset attribute.
        # Remove them for now.
        del img["srcset"]

    def _processLinkTag(self, url: str, link: Tag, local: bool = False) -> None:
        if link.get("href"):
            link["href"] = urljoin(url, link.get("href", ""))
        if local and urlsplit(link["href"]).scheme == "file":
            filepath = url2pathname(urlsplit(link["href"]).path)
            mediafilepath = mw.col.media.add_file(filepath)
            print(filepath, "===>", mediafilepath)
            link["href"] = mediafilepath
