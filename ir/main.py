import time

from PyQt5.QtCore import QObject, pyqtSlot

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

from ir.importer import Importer
from ir.settings import SettingsManager
from ir.schedule import Scheduler
from ir.util import (addMenuItem, disableOutdated, getField, getInput, isIrCard,
                     setField, viewingIrText)
from ir.view import ViewManager


class ReadingManager():
    def __init__(self):
        self.quickKeyActions = []
        self.controlsLoaded = False

        addHook('profileLoaded', self.onProfileLoaded)
        addHook('reset', self.restoreView)
        addHook('showQuestion', self.restoreView)

    def onProfileLoaded(self):
        mw.settingsManager = SettingsManager()
        mw.viewManager = ViewManager()
        self.scheduler = Scheduler()
        self.importer = Importer(mw.settingsManager.settings)

        self.settings = mw.settingsManager.settings
        mw.viewManager.settings = mw.settingsManager.settings
        self.scheduler.settings = mw.settingsManager.settings

        self.addModel()
        disableOutdated()

        if not self.controlsLoaded:
            mw.settingsManager.addMenuItem()
            self.scheduler.addMenuItem()
            addMenuItem('Read',
                        'Import Webpage',
                        self.importer.importWebpage,
                        'Alt+3')
            addMenuItem('Read',
                        'Import Feed',
                        self.importer.importFeed,
                        'Alt+4')
            mw.viewManager.addMenuItems()
            mw.viewManager.addShortcuts()
            self.controlsLoaded = True

        mw.viewManager.resetZoom('deckBrowser')

        mw.moveToState = wrap(mw.moveToState, self.setShortcuts)

    def setShortcuts(self, state, *args):
        if state == 'review':
            mw.setStateShortcuts([
                (mw.settingsManager.settings['extractKey'].lower(),
                 self.extract),
                (mw.settingsManager.settings['highlightKey'].lower(),
                 self.highlightText),
                (mw.settingsManager.settings['removeKey'].lower(),
                 self.removeText)])

    def addModel(self):
        "Only adds model if no model with the same name is present"
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
            t['qfmt'] = '<div class="ir-text">{{%s}}</div>' % (self.settings['textField'])
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
            title = getInput('Extract Text', 'Title')
            setField(newNote, self.settings['titleField'], title)
            newNote.model()['did'] = did
            mw.col.addNote(newNote)

    def restoreView(self):
        if viewingIrText():
            cid = str(mw.reviewer.card.id)
            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            if cid not in self.settings['scroll']:
                self.settings['scroll'][cid] = 0

            mw.viewManager.setZoom()
            mw.viewManager.setScroll()
            self.restoreHighlighting()

            def storePageInfo(pageInfo):
                (mw.viewManager.viewportHeight,
                 mw.viewManager.pageBottom) = pageInfo

            mw.web.evalWithCallback(
                '[window.innerHeight, document.body.scrollHeight];',
                storePageInfo)

    def restoreHighlighting(self):
        initJavaScript()
        mw.web.eval('restoreHighlighting()')

    def highlightText(self, bgColor=None, textColor=None):
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
        self.saveText()

    def saveText(self):
        def callback(text):
            if text:
                note = mw.reviewer.card.note()
                note['Text'] = text
                note.flush()
                self.restoreView()

        mw.web.evalWithCallback(
            'document.getElementsByClassName("ir-text")[0].innerHTML;',
            callback)

    def removeText(self):
        mw.web.eval('removeText()')
        self.saveText()

    def htmlUpdated(self):
        curNote = mw.reviewer.card.note()
        curNote['Text'] = mw.web.page().mainFrame().toHtml()
        curNote.flush()
        mw.web.setHtml(curNote['Text'])
        self.restoreView()

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


class IREJavaScriptCallback(QObject):
    @pyqtSlot(str)
    def htmlUpdated(self, context):
        mw.readingManager.htmlUpdated()


def initJavaScript():
    javaScript = """
    function highlight(bgColor, textColor) {
        if (window.getSelection) {
            var range, sel = window.getSelection();

            if (sel.rangeCount && sel.getRangeAt) {
                range = sel.getRangeAt(0);
            }

            document.designMode = "on";
            if (range) {
                sel.removeAllRanges();
                sel.addRange(range);
            }

            document.execCommand("foreColor", false, textColor);
            document.execCommand("hiliteColor", false, bgColor);

            document.designMode = "off";
            sel.removeAllRanges();
        }
    }

    function unhighlight(identifier) {
        var startNode, endNode;
        startNode = document.getElementById('s' + identifier);
        endNode = document.getElementById('e' + identifier);
        if (startNode) {
            range = document.createRange();
            range.setStartAfter(startNode);
            range.setEndBefore(endNode);
            sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            highlight('white', 'black');
            startNode.parentNode.removeChild(startNode);
            endNode.parentNode.removeChild(endNode);
            pyCallback.htmlUpdated('');
        }
    }

    function markRange(identifier, bgColor, textColor) {
        var range, sel = window.getSelection();
        if (sel.rangeCount && sel.getRangeAt) {
            range = sel.getRangeAt(0);
            var startNode = document.createElement('span');
            startNode.setAttribute('id', ('s' + identifier));
            startNode.setAttribute('ir-bg-color', bgColor);
            startNode.setAttribute('ir-text-color', textColor);
            range.insertNode(startNode);
            var endNode = document.createElement('span');
            endNode.setAttribute('id', ('e' + identifier));
            // editHighlightLink = document.createElement('a');
            // editHighlightLink.setAttribute('href','javascript:');
            // var tmp = ('unhighlight(' + identifier + '); return false;');
            // editHighlightLink.setAttribute('onclick', tmp);
            // sub = document.createElement('sub');
            // sub.appendChild(document.createTextNode('#'));
            // editHighlightLink.appendChild(sub);
            // endNode.appendChild(editHighlightLink);
            range.collapse(false);
            range.insertNode(endNode);
            range.setStartAfter(startNode);
            range.setEndBefore(endNode);
            sel.removeAllRanges();
            sel.addRange(range);
        }
    }

    function selectMarkedRange(identifier) {
        var startNode, endNode, range, sel;
        startNode = document.getElementById('s' + identifier);
        endNode = document.getElementById('e' + identifier);
        if (startNode && endNode) {
            range = document.createRange();
            range.setStartAfter(startNode);
            range.setEndBefore(endNode);
            sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        }
    }

    function restoreHighlighting() {
        var startNodesXPathResult = document.evaluate(
            '//*[@ir-bg-color]', document, null, XPathResult.ANY_TYPE, null);
        var sNodes = new Array();
        var startNode = startNodesXPathResult.iterateNext();
        while(startNode) {
            sNodes.push(startNode);
            startNode = startNodesXPathResult.iterateNext();
        }
        var id;
        for (var i=0; i < sNodes.length; i++) {
            startNode = sNodes[i];
            id = startNode.id.substring(1);
            selectMarkedRange(id);
            highlight(startNode.getAttribute('ir-bg-color'),
                      startNode.getAttribute('ir-text-color'))
        }
    }

    function removeText() {
        var range, sel = window.getSelection();
        if (sel.rangeCount && sel.getRangeAt) {
            range = sel.getRangeAt(0);
            var startNode = document.createElement('span');
            range.insertNode(startNode);
            var endNode = document.createElement('span');
            range.collapse(false);
            range.insertNode(endNode);
            range.setStartAfter(startNode);
            range.setEndBefore(endNode);
            sel.addRange(range);
            range.deleteContents();
        }
    }

    function getPlainText() {
        return window.getSelection().toString();
    }

    function getHtmlText() {
        var selection = window.getSelection();
        var range = selection.getRangeAt(0);
        var div = document.createElement('div');
        div.appendChild(range.cloneContents());
        return div.innerHTML;
    }
    """
    mw.web.eval(javaScript)


def answerButtonList(self, _old):
    if isIrCard():
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
    # Get the card before scheduler kicks in, else you are looking at a
    #   different card or NONE (which gives error)
    card = self.card

    _old(self, ease)

    if isIrCard():
        mw.readingManager.scheduler.scheduleCard(card, ease)


def buttonTime(self, i, _old):
    if isIrCard():
        return '<div class=spacer></div>'
    else:
        return _old(self, i)


Reviewer._answerButtonList = wrap(Reviewer._answerButtonList,
                                  answerButtonList,
                                  'around')

Reviewer._answerCard = wrap(Reviewer._answerCard, answerCard, 'around')
Reviewer._buttonTime = wrap(Reviewer._buttonTime, buttonTime, 'around')
