from collections import defaultdict

from anki.notes import Note
from aqt import mw
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.utils import getText, showInfo, tooltip

from .util import fixImages, getField, setField

SCHEDULE_EXTRACT = 0


class TextManager:
    def __init__(self):
        self.history = defaultdict(list)

    def highlight(self, bgColor=None, textColor=None):
        if not bgColor:
            bgColor = self.settings['highlightBgColor']
        if not textColor:
            textColor = self.settings['highlightTextColor']

        script = "highlight('%s', '%s');" % (bgColor, textColor)
        mw.web.eval(script)
        self.save()

    def extract(self):
        if not mw.web.selectedText():
            showInfo('Please select some text to extract.')
            return

        if self.settings['plainText']:
            mw.web.evalWithCallback('getPlainText()', self.create)
        else:
            mw.web.evalWithCallback('getHtmlText()', self.create)

    def create(self, text):
        self.highlight(self.settings['extractBgColor'],
                       self.settings['extractTextColor'])

        currentCard = mw.reviewer.card
        currentNote = currentCard.note()
        model = mw.col.models.byName(self.settings['modelName'])
        newNote = Note(mw.col, model)
        newNote.tags = currentNote.tags

        setField(newNote, self.settings['textField'], fixImages(text))
        setField(newNote,
                 self.settings['sourceField'],
                 getField(currentNote, self.settings['sourceField']))

        if self.settings['editSource']:
            EditCurrent(mw)

        if self.settings['extractDeck']:
            did = mw.col.decks.byName(self.settings['extractDeck'])['id']
        else:
            did = currentCard.did

        if self.settings['copyTitle']:
            title = getField(currentNote, self.settings['titleField'])
        else:
            title = ''

        if self.settings['editExtract']:
            setField(newNote, self.settings['titleField'], title)
            addCards = AddCards(mw)
            addCards.editor.setNote(newNote)
            deckName = mw.col.decks.get(did)['name']
            addCards.deckChooser.deck.setText(deckName)
            addCards.modelChooser.models.setText(self.settings['modelName'])
        else:
            title, accepted = getText('Enter title',
                                      title='Extract Text',
                                      default=title)
            if accepted:
                setField(newNote, self.settings['titleField'], title)
                newNote.model()['did'] = did
                mw.col.addNote(newNote)

        if self.settings['extractSchedule']:
            cards = newNote.cards()
            if cards:
                mw.readingManager.scheduler.answer(cards[0], SCHEDULE_EXTRACT)

    def remove(self):
        mw.web.eval('removeText()')
        self.save()

    def undo(self):
        note = mw.reviewer.card.note()

        if note.id not in self.history or not self.history[note.id]:
            showInfo('No undo history for this note.')
            return

        note['Text'] = self.history[note.id].pop()
        note.flush()
        mw.reset()
        tooltip('Undone')

    def save(self):
        def callback(text):
            if text:
                note = mw.reviewer.card.note()
                self.history[note.id].append(note['Text'])
                note['Text'] = text
                note.flush()

        mw.web.evalWithCallback(
            'document.getElementsByClassName("ir-text")[0].innerHTML;',
            callback)
