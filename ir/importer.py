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

from datetime import date
from ssl import _create_unverified_context
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen

from anki.notes import Note
from anki.utils import isMac
from aqt import mw
from aqt.utils import (
    chooseList,
    getText,
    showInfo,
    showCritical,
    showWarning,
    tooltip,
)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from bs4 import BeautifulSoup, Comment
from requests import get
from requests.exceptions import ConnectionError

from .lib.feedparser import parse

from .pocket import Pocket
from .util import setField


class Importer:
    pocket = None

    def _fetchWebpage(self, url):
        if isMac:
            context = _create_unverified_context()
            html = urlopen(url, context=context).read()
        else:
            headers = {'User-Agent': self.settings['userAgent']}
            html = get(url, headers=headers).content

        webpage = BeautifulSoup(html, 'html.parser')

        for tagName in self.settings['badTags']:
            for tag in webpage.find_all(tagName):
                tag.decompose()

        for c in webpage.find_all(text=lambda s: isinstance(s, Comment)):
            c.extract()

        return webpage

    def _createNote(self, title, text, source, priority=None):
        if self.settings['importDeck']:
            deck = mw.col.decks.byName(self.settings['importDeck'])
            if not deck:
                showWarning(
                    'Destination deck no longer exists. '
                    'Please update your settings.'
                )
                return
            did = deck['id']
        else:
            did = mw.col.conf['curDeck']

        model = mw.col.models.byName(self.settings['modelName'])
        note = Note(mw.col, model)
        setField(note, self.settings['titleField'], title)
        setField(note, self.settings['textField'], text)
        setField(note, self.settings['sourceField'], source)
        if priority:
            setField(note, self.settings['prioField'], priority)
        note.model()['did'] = did
        mw.col.addNote(note)
        mw.deckBrowser.show()
        return mw.col.decks.get(did)['name']

    def importWebpage(self, url=None, priority=None, silent=False):
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
        source = self.settings['sourceFormat'].format(
            date=date.today(), url='<a href="%s">%s</a>' % (url, url)
        )

        if self.settings['prioEnabled'] and not priority:
            priority = self._getPriority(webpage.title.string)

        deck = self._createNote(webpage.title.string, body, source, priority)

        if not silent:
            tooltip('Added to deck: {}'.format(deck))

        return deck

    def _getPriority(self, name=None):
        if name:
            prompt = 'Select priority for <b>{}</b>'.format(name)
        else:
            prompt = 'Select priority for import'
        return self.settings['priorities'][
            chooseList(prompt, self.settings['priorities'])
        ]

    def importFeed(self):
        url, accepted = getText('Enter URL:', title='Import Feed')

        if not url or not accepted:
            return

        if not urlsplit(url).scheme:
            url = 'http://' + url

        log = self.settings['feedLog']

        try:
            feed = parse(
                url,
                agent=self.settings['userAgent'],
                etag=log[url]['etag'],
                modified=log[url]['modified'],
            )
        except KeyError:
            log[url] = {'downloaded': []}
            feed = parse(url, agent=self.settings['userAgent'])

        if feed['status'] not in [200, 301, 302]:
            showWarning(
                'The remote server has returned an unexpected status: '
                '{}'.format(feed['status'])
            )

        if self.settings['prioEnabled']:
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
        if not self.pocket:
            self.pocket = Pocket()

        articles = self.pocket.getArticles()
        if not articles:
            return

        selected = self._select(articles)

        if self.settings['prioEnabled']:
            priority = self._getPriority()
        else:
            priority = None

        if selected:
            n = len(selected)

            mw.progress.start(
                label='Importing Pocket articles...', max=n, immediate=True
            )

            for i, article in enumerate(selected, start=1):
                deck = self.importWebpage(article['given_url'], priority, True)
                if self.settings['pocketArchive']:
                    self.pocket.archive(article)
                mw.progress.update(value=i)

            mw.progress.finish()
            tooltip('Added {} item(s) to deck: {}'.format(n, deck))

    def _select(self, choices):
        if not choices:
            return []

        dialog = QDialog(mw)
        layout = QVBoxLayout()
        listWidget = QListWidget()
        listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        for c in choices:
            item = QListWidgetItem(c['text'])
            item.setData(Qt.UserRole, c['data'])
            listWidget.addItem(item)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Close | QDialogButtonBox.Save
        )
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        buttonBox.setOrientation(Qt.Horizontal)

        layout.addWidget(listWidget)
        layout.addWidget(buttonBox)

        dialog.setLayout(layout)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.resize(500, 500)
        choice = dialog.exec_()

        if choice == 1:
            return [
                listWidget.item(i).data(Qt.UserRole)
                for i in range(listWidget.count())
                if listWidget.item(i).isSelected()
            ]
        return []
