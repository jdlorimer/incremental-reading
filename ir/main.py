# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from PyQt4.QtCore import QObject, pyqtSlot
from PyQt4.QtGui import QApplication
from PyQt4.QtWebKit import QWebPage

from anki import notes
from anki.hooks import addHook, wrap
from anki.sound import clearAudioQueue
from aqt import mw
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.reviewer import Reviewer
from aqt.utils import showWarning, tooltip

from ir.about import showAbout
from ir.settings import SettingsManager
from ir.schedule import Scheduler
from ir.text import TextManager
from ir.util import (addMenuItem,
                     addShortcut,
                     disableOutdated,
                     getField,
                     isIrCard,
                     setField,
                     viewingIrText)
from ir.view import ViewManager


class ReadingManager():
    def __init__(self):
        self.controlsLoaded = False
        self.quickKeyActions = []

        addHook('profileLoaded', self.onProfileLoaded)
        addHook('reset', self.restoreView)
        addHook('showQuestion', self.restoreView)

    def onProfileLoaded(self):
        self.settingsManager = SettingsManager()
        self.settings = self.settingsManager.settings
        self.scheduler = Scheduler(self.settings)
        self.textManager = TextManager(self.settings)
        mw.viewManager = ViewManager()
        mw.viewManager.settings = self.settings

        if not mw.col.models.byName(self.settings['modelName']):
            self.addModel()

        disableOutdated()

        if not self.controlsLoaded:
            addMenuItem('Read',
                        'Options...',
                        self.settingsManager.showDialog,
                        'Alt+1')
            addMenuItem('Read',
                        'Organizer...',
                        self.scheduler.showDialog,
                        'Alt+2')
            mw.viewManager.addMenuItems()
            mw.viewManager.addShortcuts()
            addShortcut(self.textManager.undo, self.settings['undoKey'])
            addMenuItem('Read', 'About...', showAbout)
            self.controlsLoaded = True

        mw.viewManager.resetZoom('deckBrowser')

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

    def restoreHighlighting(self):
        mw.web.page().mainFrame().addToJavaScriptWindowObject(
            'pyCallback', IREJavaScriptCallback())
        initJavaScript()
        mw.web.eval('restoreHighlighting()')

    def htmlUpdated(self):
        curNote = mw.reviewer.card.note()
        curNote['Text'] = mw.web.page().mainFrame().toHtml()
        curNote.flush()
        mw.web.setHtml(curNote['Text'])
        self.restoreView()

    def quickAdd(self, quickKey):
        if not viewingIrText():
            return

        hasSelection = False
        selectedText = ''

        if len(mw.web.selectedText()) > 0:
            hasSelection = True
            mw.web.triggerPageAction(QWebPage.Copy)
            clipboard = QApplication.clipboard()
            mimeData = clipboard.mimeData()
            if quickKey['plainText']:
                selectedText = mimeData.text()
            else:
                selectedText = mimeData.html()
            self.textManager.highlight(quickKey['bgColor'],
                                       quickKey['textColor'])

        # Create new note with selected model and deck
        newModel = mw.col.models.byName(quickKey['modelName'])
        newNote = notes.Note(mw.col, newModel)
        setField(newNote, quickKey['fieldName'], selectedText)

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

        if quickKey['editExtract']:
            addCards = AddCards(mw)
            addCards.editor.setNote(newNote)
            if newNote.stringTags():
                addCards.editor.tags.setText(newNote.stringTags().strip())
            addCards.modelChooser.models.setText(quickKey['modelName'])
            addCards.deckChooser.deck.setText(quickKey['deckName'])
        elif hasSelection:
            deckId = mw.col.decks.byName(quickKey['deckName'])['id']
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

        if quickKey['editSource']:
            EditCurrent(mw)


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
    """
    mw.web.eval(javaScript)


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
    card = self.card
    _old(self, ease)
    if isIrCard(card):
        mw.readingManager.scheduler.answer(card, ease)


def buttonTime(self, i, _old):
    if isIrCard(mw.reviewer.card):
        return '<div class=spacer></div>'
    else:
        return _old(self, i)


def keyHandler(self, evt, _old):
    key = unicode(evt.text())
    handled = False

    if viewingIrText():
        if key == mw.readingManager.settings['extractKey']:
            mw.readingManager.textManager.extract()
            handled = True
        elif key == mw.readingManager.settings['highlightKey']:
            mw.readingManager.textManager.highlight()
            handled = True
        elif key == mw.readingManager.settings['removeKey']:
            mw.readingManager.textManager.remove()
            handled = True

    if handled:
        return True
    else:
        _old(self, evt)


Reviewer._answerButtonList = wrap(Reviewer._answerButtonList,
                                  answerButtonList,
                                  'around')

Reviewer._answerCard = wrap(Reviewer._answerCard, answerCard, 'around')
Reviewer._buttonTime = wrap(Reviewer._buttonTime, buttonTime, 'around')
Reviewer._keyHandler = wrap(Reviewer._keyHandler, keyHandler, 'around')
