# Copyright 2018 Timothée Chauvin
# Copyright 2017-2018 Luo Li-Yan <joseph.lorimer13@gmail.com>
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
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen

from anki.notes import Note
from anki.utils import isMac, isWin
from aqt import mw
from aqt.utils import (askUser,
                       chooseList,
                       getText,
                       openLink,
                       showWarning,
                       tooltip)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractItemView,
                             QDialog,
                             QDialogButtonBox,
                             QListWidget,
                             QListWidgetItem,
                             QVBoxLayout)

from bs4 import BeautifulSoup, Comment
from requests import get, post

from .lib.feedparser import parse

from .util import setField


class Importer:
    def _fetchWebpage(self, url):
        if isMac:
            context = _create_unverified_context()
            html = urlopen(url, context=context).read().decode('utf-8')
        else:
            headers = {'User-Agent': self.settings['userAgent']}
            html = get(url, headers=headers).text

        webpage = BeautifulSoup(html, 'html.parser')

        for tagName in self.settings['badTags']:
            for tag in webpage.find_all(tagName):
                tag.decompose()

        for c in webpage.find_all(text=lambda s: isinstance(s, Comment)):
            c.extract()

        return webpage

    def _createNote(self, title, text, source, priority):
        if self.settings['importDeck']:
            deck = mw.col.decks.byName(self.settings['importDeck'])
            if not deck:
                showWarning('Destination deck no longer exists. '
                            'Please update your settings.')
                return
            did = deck['id']
        else:
            did = mw.col.conf['curDeck']

        model = mw.col.models.byName(self.settings['modelName'])
        note = Note(mw.col, model)
        if self.settings['prioEnabled']:
            setField(note, self.settings['priorityField'], priority)

        setField(note, self.settings['titleField'], title)
        setField(note, self.settings['textField'], text)
        setField(note, self.settings['sourceField'], source)
        note.model()['did'] = did
        mw.col.addNote(note)
        mw.deckBrowser.show()
        tooltip('Added to deck: ' + mw.col.decks.get(did)['name'])

    def importWebpage(self, url=None):
        if not url:
            url, accepted = getText('Enter URL:', title='Import Webpage')
        else:
            accepted = True

        if not url or not accepted:
            return

        if not urlsplit(url).scheme:
            url = 'http://' + url

        try:
            webpage = self._fetchWebpage(url)
        except HTTPError as error:
            showWarning('The remote server has returned an error:'
                        ' HTTP Error {} ({})'.format(
                            error.code,
                            error.reason))
            return

        body = '\n'.join(map(str, webpage.find('body').children))
        source = self.settings['sourceFormat'].format(
            date=date.today(),
            url='<a href="%s">%s</a>' % (url, url))

        if self.settings['prioEnabled']:
            priority = self.settings['priorities'][chooseList(
                'Enter priority for "' + webpage.title.string
                + '".\nYou can change it later.',
                self.settings['priorities'])]
        else:
            priority = None

        self._createNote(webpage.title.string, body, source, priority)

    def importFeed(self):
        url, accepted = getText('Enter URL:', title='Import Feed')

        if not url or not accepted:
            return

        if not urlsplit(url).scheme:
            url = 'http://' + url

        log = self.settings['feedLog']

        try:
            feed = parse(url,
                         agent=self.settings['userAgent'],
                         etag=log[url]['etag'],
                         modified=log[url]['modified'])
        except KeyError:
            log[url] = {'downloaded': []}
            feed = parse(url, agent=self.settings['userAgent'])

        if feed['status'] not in [200, 301, 302]:
            showWarning('The remote server has returned an unexpected status:'
                        ' {}'.format(feed['status']))

        entries = [{'text': e['title'], 'data': e} for e in feed['entries']]
        selected = self._select(entries)

        if selected:
            mw.progress.start(label='Importing feed entries...',
                              max=len(selected),
                              immediate=True)

            for i, entry in enumerate(selected, start=1):
                if not entry['link'] in log[url]['downloaded']:
                    self.importWebpage(entry['link'])
                    log[url]['downloaded'].append(entry['link'])
                mw.progress.update(value=i)

            log[url]['etag'] = feed.etag if hasattr(feed, 'etag') else ''
            log[url]['modified'] = (feed.modified
                                    if hasattr(feed, 'modified')
                                    else '')

            mw.progress.finish()

    def importPocket(self):
        redirectUri = 'https://github.com/luoliyan/incremental-reading-for-anki'

        if isWin:
            consumerKey = '71462-da4f02100e7e381cbc4a86df'
        elif isMac:
            consumerKey = '71462-ed224e5a561a545814023bf9'
        else:
            consumerKey = '71462-05fb63bf0314903c7e73c52f'

        response = post('https://getpocket.com/v3/oauth/request',
                        json={'consumer_key': consumerKey,
                              'redirect_uri': redirectUri},
                        headers={'X-Accept': 'application/json'})

        requestToken = response.json()['code']

        authUrl = 'https://getpocket.com/auth/authorize?'
        authParams = {'request_token': requestToken,
                      'redirect_uri': redirectUri}

        openLink(authUrl + urlencode(authParams))
        if not askUser('I have authenticated with Pocket.'):
            return

        response = post('https://getpocket.com/v3/oauth/authorize',
                        json={'consumer_key': consumerKey,
                              'code': requestToken},
                        headers={'X-Accept': 'application/json'})

        accessToken = response.json()['access_token']

        response = post('https://getpocket.com/v3/get',
                        json={'consumer_key': consumerKey,
                              'access_token': accessToken,
                              'contentType': 'article',
                              'count': 30,
                              'detailType': 'complete',
                              'sort': 'newest'},
                        headers={'X-Accept': 'application/json'})

        articles = [{'text': a['resolved_title'], 'data': a}
                    for a in response.json()['list'].values()]

        selected = self._select(articles)

        if selected:
            mw.progress.start(label='Importing Pocket articles...',
                              max=len(selected),
                              immediate=True)

            for i, article in enumerate(selected, start=1):
                self.importWebpage(article['given_url'])
                mw.progress.update(value=i)

            mw.progress.finish()

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

        buttonBox = QDialogButtonBox(QDialogButtonBox.Close |
                                     QDialogButtonBox.Save)
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
            return [listWidget.item(i).data(Qt.UserRole)
                    for i in range(listWidget.count())
                    if listWidget.item(i).isSelected()]
        else:
            return []
