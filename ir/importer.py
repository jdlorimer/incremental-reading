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

import os
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit
from urllib.request import url2pathname

from anki.notes import Note
from aqt import mw

try:
    from PyQt6.QtCore import Qt
except ModuleNotFoundError:
    from PyQt5.QtCore import Qt

from aqt.qt import (QAbstractItemView, QDialog, QDialogButtonBox, QListWidget,
                    QListWidgetItem, QVBoxLayout)
from aqt.utils import (chooseList, getFile, getText, showCritical, showInfo,
                       showWarning, tooltip)
from bs4 import BeautifulSoup, Comment, PageElement
from requests import get
from requests.exceptions import ConnectionError

from .epub import get_epub_toc
from .lib.feedparser import parse
from .pocket import Pocket
from .settings import SettingsManager
from .util import setField


class Importer:
    _pocket = None
    _settings: SettingsManager = None

    def changeProfile(self, settings: SettingsManager):
        self._settings = settings

    def _fetchWebpage(self, url):
        headers = {'User-Agent': self._settings['userAgent']}
        html = get(url, headers=headers).content
        return self._cleanWebpage(html, url)

    def _fetchLocalpage(self, filepath):
        with open(filepath, "r") as f:
            html = f.read()
            url = urlunsplit(("file", "", filepath, None, None))
            return self._cleanWebpage(html, url, True)

    def _cleanWebpage(self, html, url, local=False):
        webpage = BeautifulSoup(html, 'html.parser')

        for tagName in self._settings['badTags']:
            for tag in webpage.find_all(tagName):
                tag.decompose()

        for c in webpage.find_all(text=lambda s: isinstance(s, Comment)):
            c.extract()

        for a in webpage.find_all('a'):
            self._processATag(url, a)

        for img in webpage.find_all('img'):
            self._processImgTag(url, img, local)

        for link in webpage.find_all('link'):
            self._processLinkTag(url, link, local)

        return webpage

    def _createNote(self, title, text, source, priority=None):
        if self._settings['importDeck']:
            deck = mw.col.decks.by_name(self._settings['importDeck'])
            if not deck:
                showWarning(
                    'Destination deck no longer exists. '
                    'Please update your settings.'
                )
                return
            did = deck['id']
        else:
            did = mw.col.conf['curDeck']

        model = mw.col.models.by_name(self._settings['modelName'])
        note = Note(mw.col, model)
        setField(note, self._settings['titleField'], title)
        setField(note, self._settings['textField'], text)
        setField(note, self._settings['sourceField'], source)
        if priority:
            setField(note, self._settings['prioField'], priority)
        note.note_type()['did'] = did
        mw.col.addNote(note)
        mw.deckBrowser.show()
        return mw.col.decks.get(did)['name']

    def importWebpage(self, url=None, priority=None, silent=False, title=None):
        if not url:
            url, accepted = getText('Enter URL:', title='Import Webpage')
        else:
            accepted = True

        if not url or not accepted:
            return

        if not urlsplit(url).scheme:
            url = 'http://' + url
        elif urlsplit(url).scheme not in ['http', 'https']:
            showCritical('Only HTTP requests are supported.')
            return

        try:
            webpage = self._fetchWebpage(url)
        except HTTPError as error:
            showWarning(
                'The remote server has returned an error: '
                'HTTP Error {} ({})'.format(error.code, error.reason)
            )
            return
        except ConnectionError as error:
            showWarning('There was a problem connecting to the website.')
            return

        body = '\n'.join(map(str, webpage.find('body').children))
        source = self._settings['sourceFormat'].format(
            date=date.today(), url='<a href="%s">%s</a>' % (url, url)
        )

        if self._settings['prioEnabled'] and not priority:
            priority = self._getPriority(webpage.title.string)

        if not title:
            title = webpage.title.string or url
        deck = self._createNote(title, body, source, priority)

        if not silent:
            tooltip('Added to deck: {}'.format(deck))

        return deck

    def importLocalFile(self, filepath=None, priority=None, silent=False, title=None):
        if not filepath:
            filepath = getFile(None, 'Import Local File', None, filter="*")

        if not filepath:
            return

        filepath = Path(filepath).as_posix()  # Convert Windows Path to Linux
        if not os.path.isfile(filepath):
            showCritical('File[{}] Not exists.'.format(filepath))
            return

        try:
            webpage = self._fetchLocalpage(filepath)
        except HTTPError as error:
            showWarning(
                'The remote server has returned an error: '
                'HTTP Error {} ({})'.format(error.code, error.reason)
            )
            return
        except ConnectionError as error:
            showWarning('There was a problem connecting to the website.')
            return

        body = '\n'.join(map(str, webpage.find('body').children))
        source = self._settings['sourceFormat'].format(
            date=date.today(), url='<a href="%s">%s</a>' % (filepath, filepath)
        )

        if self._settings['prioEnabled'] and not priority:
            priority = self._getPriority(webpage.title.string)

        if not title:
            title = webpage.title.string or filepath
        deck = self._createNote(title, body, source, priority)

        if not silent:
            tooltip('Added to deck: {}'.format(deck))

        return deck

    def _getPriority(self, name=None):
        if name:
            prompt = 'Select priority for <b>{}</b>'.format(name)
        else:
            prompt = 'Select priority for import'
        return self._settings['priorities'][
            chooseList(prompt, self._settings['priorities'])
        ]

    def importFeed(self):
        url, accepted = getText('Enter URL:', title='Import Feed')

        if not url or not accepted:
            return

        if not urlsplit(url).scheme:
            url = 'http://' + url

        log = self._settings['feedLog']

        try:
            feed = parse(
                url,
                agent=self._settings['userAgent'],
                etag=log[url]['etag'],
                modified=log[url]['modified'],
            )
        except KeyError:
            log[url] = {'downloaded': []}
            feed = parse(url, agent=self._settings['userAgent'])

        if feed['status'] not in [200, 301, 302]:
            showWarning(
                'The remote server has returned an unexpected status: '
                '{}'.format(feed['status'])
            )

        if self._settings['prioEnabled']:
            priority = self._getPriority()
        else:
            priority = None

        entries = [
            {'text': e['title'], 'data': e}
            for e in feed['entries']
            if e['link'] not in log[url]['downloaded']
        ]

        if not entries:
            showInfo('There are no new items in this feed.')
            return

        selected = self._select(entries)

        if not selected:
            return

        n = len(selected)

        mw.progress.start(
            label='Importing feed entries...', max=n, immediate=True
        )

        for i, entry in enumerate(selected, start=1):
            deck = self.importWebpage(entry['link'], priority, True)
            log[url]['downloaded'].append(entry['link'])
            mw.progress.update(value=i)

        log[url]['etag'] = feed.etag if hasattr(feed, 'etag') else ''
        log[url]['modified'] = (
            feed.modified if hasattr(feed, 'modified') else ''
        )

        mw.progress.finish()
        tooltip('Added {} item(s) to deck: {}'.format(n, deck))

    def importPocket(self):
        if not self._pocket:
            self._pocket = Pocket()

        articles = self._pocket.getArticles()
        if not articles:
            return

        selected = self._select(articles)

        if self._settings['prioEnabled']:
            priority = self._getPriority()
        else:
            priority = None

        if selected:
            n = len(selected)
            mw.progress.start(
                label='Importing Pocket articles...', max=n, immediate=True
            )

            for i, article in enumerate(selected, start=1):
                deck = self.importWebpage(article['given_url'], priority, True, article['resolved_title'])
                if self._settings['pocketArchive']:
                    self._pocket.archive(article)
                mw.progress.update(value=i)

            mw.progress.finish()
            tooltip('Added {} item(s) to deck: {}'.format(n, deck))

    def importEpub(self, epub_file_path = None):
        if not epub_file_path:
            epub_file_path  = getFile(None, 'Enter epub File path', None, filter="*.epub")

        if not epub_file_path:
            return

        articles = get_epub_toc(epub_file_path)
        if not articles:
            showInfo("No articles found in {}.".format(epub_file_path))
            return
        selected = self._select(articles)

        if self._settings['prioEnabled']:
            priority = self._getPriority()
        else:
            priority = None

        if selected:
            n = len(selected)

            mw.progress.start(
                label='Importing Epub articles...', max=n, immediate=True
            )

            importedArticle = []
            for i, article in enumerate(selected, start=1):
                text = article.get('text')
                href = article['href']
                if href not in importedArticle:
                    deck = self.importLocalFile(href, priority, True, text)
                    importedArticle.append(href)
                else:
                    print(href, "Already imported, Skipping")
                mw.progress.update(value=i)

            mw.progress.finish()
            tooltip('Added {} item(s) to deck: {}'.format(len(importedArticle), deck))

    def _select(self, choices):
        if not choices:
            return []

        dialog = QDialog(mw)
        layout = QVBoxLayout()
        listWidget = QListWidget()
        listWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        for c in choices:
            item = QListWidgetItem(c['text'])
            item.setData(Qt.ItemDataRole.UserRole, c['data'])
            listWidget.addItem(item)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close | QDialogButtonBox.StandardButton.Save
        )
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        buttonBox.setOrientation(Qt.Orientation.Horizontal)

        layout.addWidget(listWidget)
        layout.addWidget(buttonBox)

        dialog.setLayout(layout)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.resize(500, 500)
        choice = dialog.exec()

        if choice == 1:
            return [
                listWidget.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(listWidget.count())
                if listWidget.item(i).isSelected()
            ]
        return []

    def _processATag(self, url: str, a: PageElement):
        if a.get('href'):
            if a['href'].startswith('#'):
                # Need to override onclick for named anchor to work
                # See https://forums.ankiweb.net/t/links-to-named-anchors-malfunction/5157
                if not a.get('onclick'):
                    named_anchor = a['href'][1:] # Remove first hash
                    a['href'] = 'javascript:;'
                    a['onclick'] = f"document.location.hash='{named_anchor}';"
            else:
                a['href'] = urljoin(url, a['href'])

    def _processImgTag(self, url: str, img: PageElement, local=False):
        if img.get('src'):
            img['src'] = urljoin(url, img.get('src', ''))
        print("src=",img['src'])
        if local and urlsplit(img['src']).scheme == "file":
            filepath = url2pathname(urlsplit(img['src']).path) 
            mediafilepath = mw.col.media.add_file(filepath)
            print(filepath, "===>", mediafilepath)
            img['src'] = mediafilepath

        # Some webpages send broken base64-encoded URI in srcset attribute.
        # Remove them for now.
        del img['srcset']

    def _processLinkTag(self, url: str, link: PageElement, local=False):
        if link.get('href'):
            link['href'] = urljoin(url, link.get('href', ''))
        if local and urlsplit(link['href']).scheme == "file":
            filepath = url2pathname(urlsplit(link['href']).path)
            mediafilepath = mw.col.media.add_file(filepath)
            print(filepath, "===>", mediafilepath)
            link['href'] = mediafilepath
