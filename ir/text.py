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

    def extract(self, settings=None):
        if not mw.web.selectedText():
            showInfo('Please select some text to extract.')
            return

        if not settings:
            settings = self.settings

        if settings['plainText']:
            mw.web.evalWithCallback(
                'getPlainText()',
                lambda text: self.create(text, settings))
        else:
            mw.web.evalWithCallback(
                'getHtmlText()',
                lambda text: self.create(text, settings))

    def create(self, text, settings):
        self.highlight(settings['extractBgColor'], settings['extractTextColor'])
        createIrNote = (settings['modelName'] == self.settings['modelName'])
        currentCard = mw.reviewer.card
        currentNote = currentCard.note()
        model = mw.col.models.byName(settings['modelName'])
        newNote = Note(mw.col, model)
        newNote.tags = currentNote.tags
        setField(newNote, settings['textField'], fixImages(text))

        if settings['extractDeck']:
            did = mw.col.decks.byName(settings['extractDeck'])['id']
        else:
            did = currentCard.did

        if createIrNote:
            if settings['copyTitle']:
                title = getField(currentNote, settings['titleField'])
            else:
                title = ''

            setField(newNote,
                     settings['sourceField'],
                     getField(currentNote, settings['sourceField']))

            if settings['editExtract']:
                setField(newNote, settings['titleField'], title)
                addCards = AddCards(mw)
                addCards.editor.setNote(newNote)
                deckName = mw.col.decks.get(did)['name']
                addCards.deckChooser.deck.setText(deckName)
                addCards.modelChooser.models.setText(settings['modelName'])
            else:
                title, accepted = getText(
                    'Enter title', title='Extract Text', default=title)
                if accepted:
                    setField(newNote, settings['titleField'], title)
                    newNote.model()['did'] = did
                    mw.col.addNote(newNote)

            if settings['scheduleExtract']:
                cards = newNote.cards()
                if cards:
                    mw.readingManager.scheduler.answer(
                        cards[0], SCHEDULE_EXTRACT)
        else:
            newNote.tags += settings['tags']
            mw.col.addNote(newNote)

        if settings['editSource']:
            EditCurrent(mw)

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
