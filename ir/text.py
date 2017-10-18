from __future__ import unicode_literals
from collections import defaultdict
import re
import time

from PyQt4.QtGui import QApplication
from PyQt4.QtWebKit import QWebPage

from anki.notes import Note
from aqt import mw
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.utils import getText, showInfo, tooltip

from BeautifulSoup import BeautifulSoup

from ir.util import getField, setField


class TextManager():
    def __init__(self, settings):
        self.settings = settings
        self.history = defaultdict(list)

    def highlight(self, bgColor=None, textColor=None):
        if not bgColor:
            bgColor = self.settings['highlightBgColor']
        if not textColor:
            textColor = self.settings['highlightTextColor']

        identifier = str(int(time.time() * 10))
        script = "markRange('%s', '%s', '%s');" % (identifier,
                                                   bgColor,
                                                   textColor)
        script += "highlight('%s', '%s');" % (bgColor, textColor)
        mw.web.eval(script)
        self.save()

    def extract(self):
        if not mw.web.selectedText():
            showInfo('Please select some text to extract.')
            return

        mw.web.triggerPageAction(QWebPage.Copy)

        mimeData = QApplication.clipboard().mimeData()

        if self.settings['plainText']:
            text = mimeData.text()
        else:
            text = mimeData.html()

        self.highlight(self.settings['extractBgColor'],
                       self.settings['extractTextColor'])

        currentCard = mw.reviewer.card
        currentNote = currentCard.note()
        model = mw.col.models.byName(self.settings['modelName'])
        newNote = Note(mw.col, model)
        newNote.tags = currentNote.tags

        setField(newNote, self.settings['textField'], text)
        setField(newNote,
                 self.settings['sourceField'],
                 getField(currentNote, self.settings['sourceField']))

        if self.settings['editSource']:
            EditCurrent(mw)

        if self.settings['extractDeck']:
            did = mw.col.decks.byName(self.settings['extractDeck'])['id']
        else:
            did = currentCard.did

        if self.settings['editExtract']:
            addCards = AddCards(mw)
            addCards.editor.setNote(newNote)
            deckName = mw.col.decks.get(did)['name']
            addCards.deckChooser.deck.setText(deckName)
            addCards.modelChooser.models.setText(self.settings['modelName'])
        else:
            title, ret = getText('Enter title:', title='Extract Text')
            if ret == 1:
                setField(newNote, self.settings['titleField'], title)
                newNote.model()['did'] = did
                mw.col.addNote(newNote)

    def remove(self):
        mw.web.eval('removeText()')
        self.save()

    def save(self):
        def removeOuterDiv(html):
            withoutOpenDiv = re.sub('^<div[^>]+>', '', unicode(html))
            withoutCloseDiv = re.sub('</div>$', '', withoutOpenDiv)
            return withoutCloseDiv

        page = mw.web.page().mainFrame().toHtml()
        soup = BeautifulSoup(page)
        irTextDiv = soup.find('div', {'class': re.compile(r'.*ir-text.*')})

        if irTextDiv:
            note = mw.reviewer.card.note()
            self.history[note.id].append(note['Text'])
            withoutDiv = removeOuterDiv(irTextDiv)
            note['Text'] = unicode(withoutDiv)
            note.flush()

    def undo(self):
        currentNote = mw.reviewer.card.note()

        if (currentNote.id not in self.history or
                not self.history[currentNote.id]):
            showInfo('No undo history for this note.')
            return

        currentNote['Text'] = self.history[currentNote.id].pop()
        currentNote.flush()
        mw.reset()
        tooltip('Undone')
