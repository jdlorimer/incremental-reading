from urllib.error import HTTPError
from urllib.parse import urlsplit

from attr import dataclass
from bs4 import BeautifulSoup
from requests import get

from ir.settings import SettingsManager

from .exceptions import ErrorLevel, ImporterError
from .html_cleaner import HtmlCleaner


@dataclass
class Webpage:
    url: str
    title: str
    body: str


class Web:
    def __init__(self, settings: SettingsManager):
        self._settings = settings
        self._htmlCleaner = HtmlCleaner()

    def download(self, url: str) -> Webpage:
        html = self._fetchWebpage(url)
        page = self._htmlCleaner.clean(html, url)
        return self._constructResponse(url, page)

    def _fetchWebpage(self, url: str) -> bytes:
        if urlsplit(url).scheme not in ["http", "https"]:
            raise ImporterError(
                ErrorLevel.CRITICAL, "Only HTTP requests are supported."
            )

        try:
            html = get(
                url, headers={"User-Agent": self._settings["userAgent"]}, timeout=5
            ).content
        except HTTPError as error:
            raise ImporterError(
                ErrorLevel.WARNING,
                f"The remote server has returned an error: HTTP Error {error.code} ({error.reason})",
            ) from error
        except ConnectionError as error:
            raise ImporterError(
                ErrorLevel.WARNING, "There was a problem connecting to the website."
            ) from error

        return html

    def _constructResponse(self, url: str, webpage: BeautifulSoup):
        try:
            body = "\n".join(map(str, webpage.find("body").children))
            title = webpage.title.string if webpage.title else url
        except AttributeError as error:
            raise ImporterError(
                ErrorLevel.WARNING, f"The webpage at {url} is not valid."
            ) from error

        return Webpage(url, title, body)
