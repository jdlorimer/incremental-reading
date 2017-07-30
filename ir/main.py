# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import time
import re

from PyQt4.QtCore import QObject, pyqtSlot
from PyQt4.QtGui import (QApplication, QDialog, QDialogButtonBox, QHBoxLayout,
                         QLabel, QLineEdit)
from PyQt4.QtWebKit import QWebPage

from anki import notes
from anki.hooks import addHook, wrap
from anki.notes import Note
from anki.sound import clearAudioQueue
from aqt import addcards, editcurrent
from aqt import mw
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.main import AnkiQt
from aqt.reviewer import Reviewer
from aqt.utils import showInfo, showWarning, tooltip

from BeautifulSoup import BeautifulSoup

from ir.settings import SettingsManager
from ir.schedule import Scheduler
from ir.util import disableOutdated, getField, isIrCard, setField, viewingIrText
from ir.view import ViewManager

TEXT_FIELD_NAME = 'Text'
SOURCE_FIELD_NAME = 'Source'
TITLE_FIELD_NAME = 'Title'

AFMT = "When do you want to see this card again?"


class ReadingManager():
    def __init__(self):
        # Track number of times add cards shortcut dialog is opened
        self.acsCount = 0
        # Track number of times vsa_resetRequiredState function is called
        #   (should be same or 1 behind acsCount)
        self.rrsCount = 0
        self.quickKeyActions = []
        self.controlsLoaded = False

        addHook('profileLoaded', self.onProfileLoaded)
        addHook('reset', self.restoreView)
        addHook('showQuestion', self.restoreView)

    def onProfileLoaded(self):
        mw.settingsManager = SettingsManager()
        mw.viewManager = ViewManager()
        self.scheduler = Scheduler()

        self.settings = mw.settingsManager.settings
        mw.viewManager.settings = mw.settingsManager.settings
        self.scheduler.settings = mw.settingsManager.settings

        self.addModel()
        disableOutdated()

        if not self.controlsLoaded:
            mw.settingsManager.addMenuItem()
            self.scheduler.addMenuItem()
            mw.viewManager.addMenuItems()
            mw.viewManager.addShortcuts()
            self.controlsLoaded = True

        mw.viewManager.resetZoom('deckBrowser')

    def addModel(self):
        "Only adds model if no model with the same name is present"
        col = mw.col
        mm = col.models
        iread_model = mm.byName(self.settings['modelName'])
        if not iread_model:
            iread_model = mm.new(self.settings['modelName'])
            model_field = mm.newField(TITLE_FIELD_NAME)
            mm.addField(iread_model, model_field)
            text_field = mm.newField(TEXT_FIELD_NAME)
            mm.addField(iread_model, text_field)
            source_field = mm.newField(SOURCE_FIELD_NAME)
            source_field['sticky'] = True
            mm.addField(iread_model, source_field)

            t = mm.newTemplate('IR Card')
            t['qfmt'] = '<div class="ir-text">{{%s}}</div>' % (TEXT_FIELD_NAME)
            t['afmt'] = AFMT

            mm.addTemplate(iread_model, t)
            mm.add(iread_model)
            return iread_model
        else:
            fmap = mm.fieldMap(iread_model)
            title_ord, title_field = fmap[TITLE_FIELD_NAME]
            text_ord, text_field = fmap[TEXT_FIELD_NAME]
            source_ord, source_field = fmap[SOURCE_FIELD_NAME]
            source_field['sticky'] = True

    def extract(self):
        if not mw.web.selectedText():
            showInfo(_('Please select some text to extract.'))
            return

        mw.web.triggerPageAction(QWebPage.Copy)

        mimeData = QApplication.clipboard().mimeData()

        if self.settings['plainText']:
            text = mimeData.text()
        else:
            text = mimeData.html()

        self.highlightText(self.settings['extractBgColor'],
                           self.settings['extractTextColor'])

        currentCard = mw.reviewer.card
        currentNote = currentCard.note()
        model = mw.col.models.byName(self.settings['modelName'])
        newNote = Note(mw.col, model)
        newNote.tags = currentNote.tags

        setField(newNote, TEXT_FIELD_NAME, text)
        setField(newNote,
                 SOURCE_FIELD_NAME,
                 getField(currentNote, SOURCE_FIELD_NAME))

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
            setField(newNote, TITLE_FIELD_NAME, self.getNewTitle())
            newNote.model()['did'] = did
            mw.col.addNote(newNote)

    def getNewTitle(self):
        dialog = QDialog(mw)
        dialog.setWindowTitle('Extract Text')
        titleLabel = QLabel('Title')
        titleEditBox = QLineEdit()
        titleEditBox.setFixedWidth(300)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(dialog.accept)
        layout = QHBoxLayout()
        layout.addWidget(titleLabel)
        layout.addWidget(titleEditBox)
        layout.addWidget(buttonBox)
        dialog.setLayout(layout)
        dialog.exec_()
        return titleEditBox.text()

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
        # No obvious/easy way to do this with BeautifulSoup
        def removeOuterDiv(html):
            withoutOpenDiv = re.sub('^<div[^>]+>', '', unicode(html))
            withoutCloseDiv = re.sub('</div>$', '', withoutOpenDiv)
            return withoutCloseDiv

        page = mw.web.page().mainFrame().toHtml()
        soup = BeautifulSoup(page)
        irTextDiv = soup.find('div', {'class': re.compile(r'.*ir-text.*')})

        if irTextDiv:
            note = mw.reviewer.card.note()
            withoutDiv = removeOuterDiv(irTextDiv)
            note['Text'] = unicode(withoutDiv)
            note.flush()
            self.restoreView()

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
            self.highlightText(quickKey['bgColor'], quickKey['textColor'])

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
            if SOURCE_FIELD_NAME == f['name']:
                setField(newNote,
                         SOURCE_FIELD_NAME,
                         getField(currentNote, SOURCE_FIELD_NAME))

        if quickKey['editExtract']:
            self.acsCount += 1
            addCards = addcards.AddCards(mw)
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


def resetRequiredState(self, oldState, _old):
    specialHandling = False
    if self.readingManager.acsCount - self.readingManager.rrsCount == 1:
        specialHandling = True
    self.readingManager.rrsCount = self.readingManager.acsCount
    if specialHandling and mw.reviewer.card:
        if oldState == 'resetRequired':
            return _old(self, 'review')
        else:
            return _old(self, oldState)
        return
    else:
        return _old(self, oldState)


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


def keyHandler(self, evt, _old):
    key = unicode(evt.text())
    handled = False

    if viewingIrText():
        if key == mw.settingsManager.settings['extractKey'].lower():
            mw.readingManager.extract()
            handled = True
        elif key == mw.settingsManager.settings['highlightKey'].lower():
            mw.readingManager.highlightText()
            handled = True
        elif key == mw.settingsManager.settings['removeKey'].lower():
            mw.readingManager.removeText()
            handled = True

    if handled:
        return True
    else:
        _old(self, evt)

AnkiQt._resetRequiredState = wrap(AnkiQt._resetRequiredState,
                                  resetRequiredState,
                                  'around')

Reviewer._answerButtonList = wrap(Reviewer._answerButtonList,
                                  answerButtonList,
                                  'around')

Reviewer._answerCard = wrap(Reviewer._answerCard, answerCard, 'around')
Reviewer._buttonTime = wrap(Reviewer._buttonTime, buttonTime, 'around')
Reviewer._keyHandler = wrap(Reviewer._keyHandler, keyHandler, 'around')
