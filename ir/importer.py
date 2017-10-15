from ssl import _create_unverified_context
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen

from anki.notes import Note
from anki.utils import isMac, isWin
from aqt import mw
from aqt.utils import askUser, openLink

from bs4 import BeautifulSoup
from requests import post

from .lib.feedparser import parse

from .util import getInput, setField


class Importer:
    def __init__(self, settings):
        self.settings = settings
        self.log = self.settings['feedLog']

    def _fetchWebpage(self, url):
        if not urlsplit(url).scheme:
            url = 'http://' + url

        if isMac:
            context = _create_unverified_context()
            html = urlopen(url, context=context).read().decode('utf-8')
        else:
            html = urlopen(url).read().decode('utf-8')

        webpage = BeautifulSoup(html, 'html.parser')

        for tagName in self.settings['badTags']:
            for tag in webpage.find_all(tagName):
                tag.decompose()

        return webpage

    def _createNote(self, title, text, source):
        did = mw.col.conf['curDeck']
        model = mw.col.models.byName(self.settings['modelName'])
        note = Note(mw.col, model)
        setField(note, self.settings['titleField'], title)
        setField(note, self.settings['textField'], text)
        setField(note, self.settings['sourceField'], source)
        note.model()['did'] = did
        mw.col.addNote(note)
        mw.deckBrowser.show()

    def importWebpage(self, url=None):
        if not url:
            url = getInput('Import Webpage', 'URL')

        if not url:
            return

        webpage = self._fetchWebpage(url)
        body = '\n'.join(map(str, webpage.find('body').children))
        self._createNote(webpage.title.string, body, url)

    def importFeed(self):
        url = getInput('Import Feed', 'URL')

        if not url:
            return

        if not urlsplit(url).scheme:
            url = 'http://' + url

        if url in self.log and self.log[url]:
            feed = parse(url,
                         etag=self.log[url]['etag'],
                         modified=self.log[url]['modified'])
        else:
            self.log[url] = {'downloaded': []}
            feed = parse(url)

        mw.progress.start(label='Importing feed entries...',
                          max=len(feed['entries']),
                          immediate=True)

        for i, entry in enumerate(feed['entries'], start=1):
            if not entry['link'] in self.log[url]['downloaded']:
                self.importWebpage(entry['link'])
                self.log[url]['downloaded'].append(entry['link'])
            mw.progress.update(value=i)

        self.log[url]['etag'] = feed.etag if hasattr(feed, 'etag') else ''
        self.log[url]['modified'] = (feed.modified
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
                              'count': 10,
                              'detailType': 'complete',
                              'sort': 'newest'},
                        headers={'X-Accept': 'application/json'})

        mw.progress.start(label='Importing Pocket articles...',
                          max=len(response.json()['list']),
                          immediate=True)

        for i, article in enumerate(response.json()['list'].values(), start=1):
            self.importWebpage(article['resolved_url'])
            mw.progress.update(value=i)

        mw.progress.finish()
