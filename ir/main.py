from anki import notes
from anki.hooks import addHook, wrap
from anki.sound import clearAudioQueue
from aqt import mw
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.reviewer import Reviewer
from aqt.utils import showWarning, tooltip

import sip

from .about import showAbout
from .importer import Importer
from .schedule import Scheduler
from .settings import SettingsManager
from .text import TextManager
from .util import (addMenuItem,
                   getField,
                   isIrCard,
                   setField,
                   viewingIrText)
from .view import ViewManager


class ReadingManager:
    def __init__(self):
        self.importer = Importer()
        self.scheduler = Scheduler()
        self.settingsManager = SettingsManager()
        self.textManager = TextManager()
        self.viewManager = ViewManager()
        addHook('profileLoaded', self.onProfileLoaded)
        addHook('reviewStateShortcuts', self.setShortcuts)
        addHook('prepareQA', self.onPrepareQA)
        addHook('showAnswer', self.onShowAnswer)
        addHook('reviewCleanup', self.onReviewCleanup)
        self.qshortcuts = []

    def onProfileLoaded(self):
        self.settings = self.settingsManager.loadSettings()
        self.importer.settings = self.settings
        self.scheduler.settings = self.settings
        self.textManager.settings = self.settings
        self.viewManager.settings = self.settings
        self.viewManager.resetZoom('deckBrowser')
        self.addModel()
        self.loadMenuItems()
        self.shortcuts = [(self.settings['extractKey'],
                           self.textManager.extract),
                          (self.settings['highlightKey'],
                          self.textManager.highlight),
                          (self.settings['removeKey'], self.textManager.remove),
                          (self.settings['undoKey'], self.textManager.undo),
                          ('Up', self.viewManager.lineUp),
                          ('Down', self.viewManager.lineDown),
                          ('PgUp', self.viewManager.pageUp),
                          ('PgDown', self.viewManager.pageDown)]

    def loadMenuItems(self):
        if hasattr(mw, 'customMenus') and 'Read' in mw.customMenus:
            mw.customMenus['Read'].clear()

        addMenuItem('Read',
                    'Options...',
                    self.settingsManager.showDialog,
                    'Alt+1')
        addMenuItem('Read', 'Organizer...', self.scheduler.showDialog, 'Alt+2')
        addMenuItem('Read',
                    'Import Webpage',
                    self.importer.importWebpage,
                    'Alt+3')
        addMenuItem('Read', 'Import Feed', self.importer.importFeed, 'Alt+4')
        addMenuItem('Read',
                    'Import Pocket',
                    self.importer.importPocket,
                    'Alt+5')
        addMenuItem('Read', 'Zoom In', self.viewManager.zoomIn, 'Ctrl++')
        addMenuItem('Read', 'Zoom Out', self.viewManager.zoomOut, 'Ctrl+-')
        addMenuItem('Read', 'About...', showAbout)

        self.settingsManager.loadMenuItems()

    def onPrepareQA(self, html, card, context):
        easyShortcut = next(
            (s for s in mw.stateShortcuts if s.key().toString() == '4'), None)

        if isIrCard(card):
            if context == 'reviewQuestion':
                self.qshortcuts = mw.applyShortcuts(self.shortcuts)
                mw.stateShortcuts += self.qshortcuts
            if easyShortcut:
                mw.stateShortcuts.remove(easyShortcut)
                sip.delete(easyShortcut)
        elif not easyShortcut:
            mw.stateShortcuts += mw.applyShortcuts(
                [('4', lambda: mw.reviewer._answerCard(4))])

        return html

    def onShowAnswer(self):
        for qs in self.qshortcuts:
            mw.stateShortcuts.remove(qs)
            sip.delete(qs)

    def onReviewCleanup(self):
        self.qshortcuts = []

    def setShortcuts(self, shortcuts):
        shortcuts.append(('Ctrl+=', self.viewManager.zoomIn))

    def addModel(self):
        if mw.col.models.byName(self.settings['modelName']):
            return

        model = mw.col.models.new(self.settings['modelName'])

        titleField = mw.col.models.newField(self.settings['titleField'])
        textField = mw.col.models.newField(self.settings['textField'])
        sourceField = mw.col.models.newField(self.settings['sourceField'])
        sourceField['sticky'] = True

        mw.col.models.addField(model, titleField)
        mw.col.models.addField(model, textField)
        mw.col.models.addField(model, sourceField)

        template = mw.col.models.newTemplate('IR Card')
        template['qfmt'] = '<div class="ir-text">{{%s}}</div>' % (
            self.settings['textField'])
        template['afmt'] = 'When do you want to see this card again?'

        mw.col.models.addTemplate(model, template)
        mw.col.models.add(model)

    def quickAdd(self, quickKey):
        if not viewingIrText():
            return

        self.currentQuickKey = quickKey

        if quickKey['plainText']:
            mw.web.evalWithCallback('getPlainText()', self.createNote)
        else:
            mw.web.evalWithCallback('getHtmlText()', self.createNote)

    def createNote(self, selectedText):
        self.textManager.highlight(self.currentQuickKey['bgColor'],
                                   self.currentQuickKey['textColor'])

        newModel = mw.col.models.byName(self.currentQuickKey['modelName'])
        newNote = notes.Note(mw.col, newModel)
        setField(newNote, self.currentQuickKey['fieldName'], selectedText)

        card = mw.reviewer.card
        currentNote = card.note()
        tags = currentNote.stringTags()
        # Sets tags for the note, but still have to set them in the editor
        #   if show dialog (see below)
        newNote.setTagsFromStr(tags)

        for f in newModel['flds']:
            if self.settings['sourceField'] == f['name']:
                setField(newNote,
                         self.settings['sourceField'],
                         getField(currentNote, self.settings['sourceField']))

        if self.currentQuickKey['editExtract']:
            addCards = AddCards(mw)
            addCards.editor.setNote(newNote)
            if newNote.stringTags():
                addCards.editor.tags.setText(newNote.stringTags().strip())
            addCards.modelChooser.models.setText(
                self.currentQuickKey['modelName'])
            addCards.deckChooser.deck.setText(
                self.currentQuickKey['deckName'])
        else:
            deckId = mw.col.decks.byName(self.currentQuickKey['deckName'])['id']
            newNote.model()['did'] = deckId
            ret = newNote.dupeOrEmpty()
            if ret == 1:
                showWarning(_(
                    'The first field is empty.'),
                    help='AddItems#AddError')
                return
            cards = mw.col.addNote(newNote)
            if not cards:
                showWarning(_('''\
                    The input you have provided would make an empty \
                    question on all cards.'''), help='AddItems')
                return

            clearAudioQueue()
            mw.col.autosave()
            tooltip(_('Added'))

        if self.currentQuickKey['editSource']:
            EditCurrent(mw)


def answerButtonList(self, _old):
    if isIrCard(self.card):
        return ((1, _('Soon')), (2, _('Later')), (3, _('Custom')))
    else:
        return _old(self)


def answerCard(self, ease, _old):
    card = self.card
    _old(self, ease)
    if isIrCard(card):
        mw.readingManager.scheduler.answer(card, ease)


def buttonTime(self, i, _old):
    if isIrCard(mw.reviewer.card):
        return '<div class=spacer></div>'
    else:
        return _old(self, i)


Reviewer._answerButtonList = wrap(Reviewer._answerButtonList,
                                  answerButtonList,
                                  'around')

Reviewer._answerCard = wrap(Reviewer._answerCard, answerCard, 'around')
Reviewer._buttonTime = wrap(Reviewer._buttonTime, buttonTime, 'around')
