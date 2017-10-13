import os

from anki import notes
from anki.hooks import addHook, wrap
from anki.sound import clearAudioQueue
from aqt import mw
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.reviewer import Reviewer
from aqt.utils import showWarning, tooltip

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
        self.controlsLoaded = False
        self.quickKeyActions = []

        addHook('profileLoaded', self.onProfileLoaded)
        addHook('prepareQA', self.restoreView)

        moduleDir, _ = os.path.split(__file__)
        jsFilePath = os.path.join(moduleDir, 'javascript.js')
        with open(jsFilePath, encoding='utf-8') as jsFile:
            self.mainJavaScript = jsFile.read()

    def onProfileLoaded(self):
        self.settingsManager = SettingsManager()
        self.settings = self.settingsManager.settings
        self.importer = Importer(self.settings)
        self.scheduler = Scheduler(self.settings)
        self.textManager = TextManager(self.settings)
        self.viewManager = ViewManager(self.settings)

        if not mw.col.models.byName(self.settings['modelName']):
            self.addModel()

        if not self.controlsLoaded:
            self.loadControls()
            self.controlsLoaded = True

        addHook('reviewStateShortcuts', self.setShortcuts)

    def loadControls(self):
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
        addMenuItem('Read', 'Zoom In', self.viewManager.zoomIn, 'Ctrl++')
        addMenuItem('Read', 'Zoom Out', self.viewManager.zoomOut, 'Ctrl+-')
        addMenuItem('Read', 'About...', showAbout)

    def setShortcuts(self, shortcuts):
        shortcuts += [(self.settings['extractKey'], self.textManager.extract),
                      (self.settings['highlightKey'],
                       self.textManager.highlight),
                      (self.settings['removeKey'], self.textManager.remove),
                      (self.settings['undoKey'], self.textManager.undo),
                      ('Up', self.viewManager.lineUp),
                      ('Down', self.viewManager.lineDown),
                      ('PgUp', self.viewManager.pageUp),
                      ('PgDown', self.viewManager.pageDown),
                      ('Ctrl+=', self.viewManager.zoomIn)]

    def addModel(self):
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

            self.viewManager.setZoom()

            def storePageInfo(pageInfo):
                (self.viewManager.viewportHeight,
                 self.viewManager.pageBottom) = pageInfo

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
