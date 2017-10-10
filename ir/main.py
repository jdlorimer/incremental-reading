from collections import defaultdict
import os

from anki import notes
from anki.hooks import addHook, wrap
from anki.notes import Note
from anki.sound import clearAudioQueue
from aqt import addcards, editcurrent
from aqt import mw
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.reviewer import Reviewer
from aqt.utils import showInfo, showWarning, tooltip

from .about import showAbout
from .importer import Importer
from .schedule import Scheduler
from .settings import SettingsManager
from .util import (addMenuItem, addShortcut, fixImages, getField, getInput,
                   isIrCard, setField, viewingIrText)
from .view import ViewManager


class ReadingManager:
    def __init__(self):
        self.controlsLoaded = False
        self.textHistory = defaultdict(list)
        self.quickKeyActions = []

        addHook('profileLoaded', self.onProfileLoaded)
        addHook('prepareQA', self.restoreView)

        moduleDir, _ = os.path.split(__file__)
        jsFilePath = os.path.join(moduleDir, 'javascript.js')
        with open(jsFilePath, encoding='utf-8') as jsFile:
            self.mainJavaScript = jsFile.read()

    def onProfileLoaded(self):
        mw.settingsManager = SettingsManager()
        mw.viewManager = ViewManager()
        self.scheduler = Scheduler()
        self.importer = Importer(mw.settingsManager.settings)

        self.settings = mw.settingsManager.settings
        mw.viewManager.settings = mw.settingsManager.settings
        self.scheduler.settings = mw.settingsManager.settings

        self.addModel()

        if not self.controlsLoaded:
            self.loadControls()
            self.controlsLoaded = True

        mw.viewManager.resetZoom('deckBrowser')
        addHook('reviewStateShortcuts', self.setShortcuts)

    def loadControls(self):
        mw.settingsManager.addMenuItem()
        self.scheduler.addMenuItem()
        addMenuItem('Read', 'Import Webpage',
                    self.importer.importWebpage,
                    'Alt+3')
        addMenuItem('Read',
                    'Import Feed',
                    self.importer.importFeed,
                    'Alt+4')
        addShortcut(self.undo, self.settings['undoKey'])
        mw.viewManager.addMenuItems()
        mw.viewManager.addShortcuts()
        addMenuItem('Read', 'About...', showAbout)

    def setShortcuts(self, shortcuts):
        shortcuts += [(mw.settingsManager.settings['extractKey'].lower(),
                       self.extract),
                      (mw.settingsManager.settings['highlightKey'].lower(),
                       self.highlightText),
                      (mw.settingsManager.settings['removeKey'].lower(),
                       self.removeText)]

    def addModel(self):
        col = mw.col
        mm = col.models
        iread_model = mm.byName(self.settings['modelName'])
        if not iread_model:
            iread_model = mm.new(self.settings['modelName'])
            model_field = mm.newField(self.settings['titleField'])
            mm.addField(iread_model, model_field)
            text_field = mm.newField(self.settings['textField'])
            mm.addField(iread_model, text_field)
            source_field = mm.newField(self.settings['sourceField'])
            source_field['sticky'] = True
            mm.addField(iread_model, source_field)

            t = mm.newTemplate('IR Card')
            t['qfmt'] = '<div class="ir-text">{{%s}}</div>' % (
                self.settings['textField'])
            t['afmt'] = 'When do you want to see this card again?'

            mm.addTemplate(iread_model, t)
            mm.add(iread_model)
            return iread_model
        else:
            fmap = mm.fieldMap(iread_model)
            title_ord, title_field = fmap[self.settings['titleField']]
            text_ord, text_field = fmap[self.settings['textField']]
            source_ord, source_field = fmap[self.settings['sourceField']]
            source_field['sticky'] = True

    def extract(self):
        if not mw.web.selectedText():
            showInfo(_('Please select some text to extract.'))
            return

        if self.settings['plainText']:
            mw.web.evalWithCallback('getPlainText()', self.createExtractNote)
        else:
            mw.web.evalWithCallback('getHtmlText()', self.createExtractNote)

    def createExtractNote(self, text):
        self.highlightText(self.settings['extractBgColor'],
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

        if self.settings['editExtract']:
            addCards = AddCards(mw)
            addCards.editor.setNote(newNote)
            deckName = mw.col.decks.get(did)['name']
            addCards.deckChooser.deck.setText(deckName)
            addCards.modelChooser.models.setText(self.settings['modelName'])
        else:
            title = getInput('Extract Text', 'Title')
            setField(newNote, self.settings['titleField'], title)
            newNote.model()['did'] = did
            mw.col.addNote(newNote)

    def restoreView(self, html, card, context):
        javaScript = ''
        limitWidthScript = '''
            <script>
            if (screen.width > {maxWidth} ) {{
                var styleSheet = document.styleSheets[0];
                styleSheet.insertRule(
                    "div {{ width: {maxWidth}px; margin: 20px auto }}");
            }}
            </script>'''.format(maxWidth=self.settings['maxWidth'])

        if (card.model()['name'] == self.settings['modelName'] and
                context == 'reviewQuestion'):
            cid = str(card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            if cid not in self.settings['scroll']:
                self.settings['scroll'][cid] = 0

            mw.viewManager.setZoom()

            def storePageInfo(pageInfo):
                (mw.viewManager.viewportHeight,
                 mw.viewManager.pageBottom) = pageInfo

            mw.web.evalWithCallback(
                '[window.innerHeight, document.body.scrollHeight];',
                storePageInfo)

            savedPos = self.settings['scroll'][cid]

            javaScript = '''
                <script>
                %s

                function restoreScroll() {
                    window.scrollTo(0, %s);
                }

                onUpdateHook.push(restoreScroll);
                </script>''' % (self.mainJavaScript, savedPos)

            if self.settings['limitWidth']:
                javaScript = limitWidthScript + javaScript

        elif self.settings['limitGlobalWidth']:
            javaScript = limitWidthScript

        return html + javaScript

    def highlightText(self, bgColor=None, textColor=None):
        if not bgColor:
            bgColor = self.settings['highlightBgColor']
        if not textColor:
            textColor = self.settings['highlightTextColor']

        script = "highlight('%s', '%s');" % (bgColor, textColor)
        mw.web.eval(script)
        self.saveText()

    def saveText(self):
        def callback(text):
            if text:
                note = mw.reviewer.card.note()
                self.textHistory[note.id].append(note['Text'])
                note['Text'] = text
                note.flush()

        mw.web.evalWithCallback(
            'document.getElementsByClassName("ir-text")[0].innerHTML;',
            callback)

    def removeText(self):
        mw.web.eval('removeText()')
        self.saveText()

    def undo(self):
        currentNote = mw.reviewer.card.note()

        if (currentNote.id not in self.textHistory or
                not self.textHistory[currentNote.id]):
            showInfo('No undo history for this note.')
            return

        currentNote['Text'] = self.textHistory[currentNote.id].pop()
        currentNote.flush()
        mw.reset()
        tooltip('Undone.')

    def quickAdd(self, quickKey):
        if not viewingIrText():
            return

        self.currentQuickKey = quickKey

        if quickKey['plainText']:
            mw.web.evalWithCallback('getPlainText()', self.createNote)
        else:
            mw.web.evalWithCallback('getHtmlText()', self.createNote)

    def createNote(self, selectedText):
        self.highlightText(self.currentQuickKey['bgColor'],
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
            addCards = addcards.AddCards(mw)
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
            self.editCurrent = editcurrent.EditCurrent(mw)


def answerButtonList(self, _old):
    if isIrCard(mw.reviewer.card):
        l = ((1, _("Soon")),)
        cnt = mw.col.sched.answerButtons(self.card)
        if cnt == 2:
            return l + ((2, _("Later")),)
        elif cnt == 3:
            return l + ((2, _("Later")), (3, _("Custom")))
        else:
            return l + ((2, _("Later")), (3, _("MuchLater")), (4, _("Custom")))
    else:
        return _old(self)


def answerCard(self, ease, _old):
    card = self.card  # Copy card reference, before scheduler changes it
    _old(self, ease)
    if isIrCard(card):
        mw.readingManager.scheduler.scheduleCard(card, ease)


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
