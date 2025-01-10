# Copyright 2018 Timothée Chauvin
# Copyright 2017-2019 Joseph Lorimer <joseph@lorimer.me>
#
# Permission to use, copy, modify, and distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright
# notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

from typing import Optional

from .local_file import LocalFile
from .web import Web

try:
    from PyQt6.QtCore import Qt
except ModuleNotFoundError:
    from PyQt5.QtCore import Qt

from ir.settings import SettingsManager

from .concrete_importers import (
    EpubImporter,
    FeedImporter,
    PocketImporter,
    WebpageImporter,
)
from .pocket import Pocket


class Importer:
    _pocket: Optional[Pocket] = None
    _web: Optional[Web] = None
    _localFile: Optional[LocalFile] = None
    _settings: Optional[SettingsManager] = None

    _webImporter: Optional[WebpageImporter] = None
    _feedImporter: Optional[FeedImporter] = None
    _epubImporter: Optional[EpubImporter] = None
    _pocketImporter: Optional[PocketImporter] = None

    def changeProfile(self, settings: SettingsManager):
        self._settings = settings

        self._web = Web(self._settings)
        self._localFile = LocalFile()
        self._pocket = Pocket()

        self._webImporter = WebpageImporter(self._settings, self._web)
        self._feedImporter = FeedImporter(self._settings, self._web)
        self._epubImporter = EpubImporter(self._settings, self._localFile)
        self._pocketImporter = PocketImporter(self._settings, self._pocket, self._web)

    def importWebpage(self):
        self._webImporter.importContent()

    def importFeed(self):
        self._feedImporter.importContent()

    def importPocket(self):
        self._pocketImporter.importContent()

    def importEpub(self):
        self._epubImporter.importContent()
