# Copyright 2013 Tiago Barroso
# Copyright 2013 Frank Kmiec
# Copyright 2013-2016 Aleksej
# Copyright 2017 Christian Weiß
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

from collections import defaultdict

from anki.decks import DeckId
from anki.notes import Note
from aqt import mw
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.utils import getText, showInfo, showWarning, tooltip

from .settings import SettingsManager
from .util import fixImages, getField, setField

SCHEDULE_EXTRACT = 0


class TextManager:
    _history = defaultdict(list)
    _settings: SettingsManager = None

    def changeProfile(self, settings: SettingsManager):
        self._settings = settings

    def highlight(self, bgColor=None, textColor=None):
        if not bgColor:
            bgColor = self._settings['highlightBgColor']
        if not textColor:
            textColor = self._settings['highlightTextColor']

        script = "highlight('%s', '%s')" % (bgColor, textColor)
        mw.web.eval(script)
        self.save()

    def format(self, style):
        mw.web.eval('format("%s")' % style)
        self.save()

    def toggleOverlay(self):
        mw.web.eval('toggleOverlay()')
        self.save()

    def extract(self, settings=None):
        if mw.state != 'review':
            return

        if not settings:
            settings = self._settings

        if not mw.web.selectedText() and not settings['editExtract']:
            showInfo('Please select some text to extract.')
            return

        if settings['plainText']:
            mw.web.evalWithCallback(
                'getPlainText()', lambda text: self.create(text, settings)
            )
        else:
            mw.web.evalWithCallback(
                'getHtmlText()', lambda text: self.create(text, settings)
            )

    def create(self, text, settings):
        currentCard = mw.reviewer.card
        currentNote = currentCard.note()
        model = mw.col.models.by_name(settings['modelName'])
        newNote = Note(mw.col, model)
        newNote.tags = currentNote.tags
        setField(newNote, settings['textField'], fixImages(text))

        if settings['extractDeck']:
            deck = mw.col.decks.by_name(settings['extractDeck'])
            if not deck:
                showWarning(
                    'Destination deck no longer exists. '
                    'Please update your settings.'
                )
                return
            did = deck['id']
        else:
            did = currentCard.did

        if settings['isQuickKey']:
            newNote.tags += settings['tags']

            if settings['sourceField']:
                setField(
                    newNote,
                    settings['sourceField'],
                    getField(currentNote, self._settings['sourceField']),
                )

            if settings['editExtract']:
                highlight = self._editExtract(newNote, did, settings)
            else:
                highlight = True
                newNote.note_type()['did'] = did
                mw.col.addNote(newNote)
        else:
            if settings['copyTitle']:
                title = getField(currentNote, settings['titleField'])
            else:
                title = ''

            setField(
                newNote,
                settings['sourceField'],
                getField(currentNote, settings['sourceField']),
            )
            if settings['prioEnabled']:
                setField(
                    newNote,
                    settings['prioField'],
                    getField(currentNote, settings['prioField']),
                )

            if settings['editExtract']:
                setField(newNote, settings['titleField'], title)
                highlight = self._editExtract(newNote, did, settings)
            else:
                highlight = self._getTitle(newNote, did, title, settings)

            if settings['scheduleExtract'] and not settings['prioEnabled']:
                cards = newNote.cards()
                if cards:
                    mw.readingManager.scheduler.answer(
                        cards[0], SCHEDULE_EXTRACT
                    )

        if highlight:
            self.highlight(
                settings['extractBgColor'], settings['extractTextColor']
            )

        if settings['editSource']:
            EditCurrent(mw)

    def _editExtract(self, note: Note, deckId: DeckId, settings: SettingsManager):
        def onAdd():
            self.highlight(
                settings['extractBgColor'], settings['extractTextColor']
            )

        addCards = AddCards(mw)
        addCards.set_note(note, deckId)
        addCards.addButton.clicked.connect(onAdd)

        # Do not highlight immediately, but only after the card is added
        return False

    def _getTitle(self, note, did, title, settings):
        title, accepted = getText(
            'Enter title', title='Extract Text', default=title
        )

        if accepted:
            setField(note, settings['titleField'], title)
            note.note_type()['did'] = did
            mw.col.addNote(note)

        return accepted

    def remove(self):
        mw.web.eval('removeText()')
        self.save()

    def undo(self):
        note = mw.reviewer.card.note()

        if note.id not in self._history or not self._history[note.id]:
            showInfo('No undo history for this note.')
            return

        note['Text'] = self._history[note.id].pop()
        #note.flush()
        mw.col.update_note(note)
        mw.reset()
        tooltip('Undone')

    def save(self):
        def callback(text):
            if text:
                note = mw.reviewer.card.note()
                self._history[note.id].append(note['Text'])
                note['Text'] = text
                #note.flush()
                mw.col.update_note(note)

        mw.web.evalWithCallback(
            'document.getElementsByClassName("ir-text")[0].innerHTML;',
            callback,
        )
