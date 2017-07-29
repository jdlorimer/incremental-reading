from urllib.request import urlopen

from anki.notes import Note
from aqt import mw

from bs4 import BeautifulSoup

from ir.util import getInput, setField


class Importer:
    def importWebpage(self):
        model = mw.col.models.byName(self.settings['modelName'])
        newNote = Note(mw.col, model)
        url = getInput('Import Webpage', 'URL')
        title = getInput('Import Webpage', 'Title')
        html = urlopen(url).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        for iframe in soup.find_all('iframe'):
            iframe.decompose()
        setField(newNote, self.settings['titleField'], title)
        setField(newNote, self.settings['textField'], str(soup))
        setField(newNote, self.settings['sourceField'], url)
        did = mw.col.decks.byName(self.settings['importDeck'])['id']
        newNote.model()['did'] = did
        mw.col.addNote(newNote)
        mw.deckBrowser.refresh()
