from pathlib import Path
from urllib.parse import urlunsplit

from attr import dataclass
from bs4 import BeautifulSoup

from .exceptions import ErrorLevel, ImporterError
from .html_cleaner import HtmlCleaner


@dataclass
class ParsedFile:
    body: str


class LocalFile:
    def __init__(self) -> None:
        self._htmlCleaner = HtmlCleaner()

    def process(self, filepath: str) -> ParsedFile:
        if not filepath:
            raise ValueError("Filepath is empty")

        filepath = Path(filepath).as_posix()  # Convert Windows Path to Linux

        html = self._fetchLocalPage(filepath)

        url = urlunsplit(("file", "", filepath, None, None))
        page = self._htmlCleaner.clean(html, url, True)

        return self._constructResponse(page)

    def _fetchLocalPage(self, filepath: str) -> str:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as error:
            raise ImporterError(
                ErrorLevel.CRITICAL, f"File [{filepath}] Not exists."
            ) from error

    def _constructResponse(self, localPage: BeautifulSoup) -> ParsedFile:
        body = "\n".join(map(str, localPage.find("body").children))
        return ParsedFile(body)
