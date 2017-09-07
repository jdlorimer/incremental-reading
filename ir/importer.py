from urllib.request import urlopen
from urllib.parse import urlsplit

from anki.notes import Note
from aqt import mw

from bs4 import BeautifulSoup

from .lib.feedparser import parse

from .util import getInput, setField


class Importer:
    def __init__(self, settings):
        self.settings = settings
        self.log = self.settings['feedLog']

    def _fetchWebpage(self, url):
        if not urlsplit(url).scheme:
            url = 'http://' + url

        html = urlopen(url).read().decode('utf-8')
        webpage = BeautifulSoup(html, 'html.parser')

        for tagName in self.settings['badTags']:
            for tag in webpage.find_all(tagName):
                tag.decompose()

        return webpage

    def _createNote(self, title, text, source):
        did = mw.col.decks.byName(self.settings['importDeck'])['id']
        model = mw.col.models.byName(self.settings['modelName'])
        newNote = Note(mw.col, model)
        setField(newNote, self.settings['titleField'], title)
        setField(newNote, self.settings['textField'], text)
        setField(newNote, self.settings['sourceField'], source)
        newNote.model()['did'] = did
        mw.col.addNote(newNote)
        mw.deckBrowser.refresh()

    def importWebpage(self):
        url = getInput('Import Webpage', 'URL')
        webpage = self._fetchWebpage(url)
        body = '\n'.join(map(str, webpage.find('body').children))
        self._createNote(webpage.title.string, body, url)

    def importFeed(self):
        url = getInput('Import Feed', 'URL')

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
                webpage = self._fetchWebpage(entry['link'])
                body = '\n'.join(map(str, webpage.find('body').children))
                self._createNote(webpage.title.string, body, entry['link'])
                self.log[url]['downloaded'].append(entry['link'])
            mw.progress.update(value=i)

        self.log[url]['etag'] = feed.etag if hasattr(feed, 'etag') else ''
        self.log[url]['modified'] = feed.modified if hasattr(feed, 'modified') else ''

        mw.progress.finish()
