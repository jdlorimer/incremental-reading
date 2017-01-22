# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re

from PyQt4.QtCore import QObject, QPoint, Qt, SIGNAL, SLOT, pyqtSlot
from PyQt4.QtGui import QApplication, QDialog, QDialogButtonBox, QVBoxLayout
from PyQt4.QtWebKit import QWebPage
from anki import notes
from anki.hooks import addHook, wrap
from anki.sound import clearAudioQueue
from aqt import addcards, editcurrent, mw
from aqt.main import AnkiQt
from aqt.utils import showWarning, tooltip
from aqt.webview import AnkiWebView

from ir.util import addMenuItem, addShortcut, getField, setField

IR_MODEL_NAME = 'IR3'
SOURCE_FIELD_NAME = 'Source'


class ViewManager():
    def __init__(self):
        # Variable to hold quick keys
        self.quickKeys = {};
        self.lastDialogQuickKey = {};
        # Track number of times add cards shortcut dialog is opened
        self.acsCount = 0;
        # Track number of times vsa_resetRequiredState function is called (should be same or 1 behind acsCount)
        self.rrsCount = 0;
        # Track number of times vsa_reviewState function is called (should be same or 1 behind acsCount)
        self.rsCount = 0;

        self.controlsLoaded = False
        self.previousState = None

    def zoomIn(self):
        if mw.reviewer.card:
            if mw.reviewer.card.model()['name'] == IR_MODEL_NAME:
                cardID = str(mw.reviewer.card.id)

                if cardID not in self.settings['zoom']:
                    self.settings['zoom'][cardID] = 1

                self.settings['zoom'][cardID] += self.settings['zoomStep']
                mw.web.setTextSizeMultiplier(self.settings['zoom'][cardID])
            else:
                newFactor = mw.web.textSizeMultiplier() + self.settings['zoomStep']
                mw.web.setTextSizeMultiplier(newFactor)


    def zoomOut(self):
        if mw.reviewer.card:
            if mw.reviewer.card.model()['name'] == IR_MODEL_NAME:
                cardID = str(mw.reviewer.card.id)

                if cardID not in self.settings['zoom']:
                    self.settings['zoom'][cardID] = 1

                self.settings['zoom'][cardID] -= self.settings['zoomStep']
                mw.web.setTextSizeMultiplier(self.settings['zoom'][cardID])
            else:
                newFactor = mw.web.textSizeMultiplier() - self.settings['zoomStep']
                mw.web.setTextSizeMultiplier(newFactor)

    def setScrollPosition(self, newPosition):
        mw.web.page().mainFrame().setScrollPosition(QPoint(0, newPosition))
        self.saveScrollPosition()

    def saveScrollPosition(self):
        if (mw.reviewer.card and
            mw.reviewer.state == 'question' and
            mw.state == 'review'):
            currentPosition = mw.web.page().mainFrame().scrollPosition().y()
            self.settings['scroll'][str(mw.reviewer.card.id)] = currentPosition

    def pageUp(self):
        currentPosition = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['pageScrollFactor']
        newPosition = max(0, (currentPosition - movementSize))
        self.setScrollPosition(newPosition)

    def pageDown(self):
        currentPosition = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['pageScrollFactor']
        pageBottom = mw.web.page().mainFrame().scrollBarMaximum(Qt.Vertical)
        newPosition = min(pageBottom, (currentPosition + movementSize))
        self.setScrollPosition(newPosition)

    def lineUp(self):
        currentPosition = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['lineScrollFactor']
        newPosition = max(0, (currentPosition - movementSize))
        self.setScrollPosition(newPosition)

    def lineDown(self):
        currentPosition = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['lineScrollFactor']
        pageBottom = mw.web.page().mainFrame().scrollBarMaximum(Qt.Vertical)
        newPosition = min(pageBottom, (currentPosition + movementSize))
        self.setScrollPosition(newPosition)

    def addShortcuts(self):
        addShortcut(self.lineUp, 'Up')
        addShortcut(self.lineDown, 'Down')
        addShortcut(self.pageUp, 'PgUp')
        addShortcut(self.pageDown, 'PgDown')
        addShortcut(self.zoomIn, 'Ctrl+=')

    def addMenuItems(self):
        addMenuItem('Read', 'Zoom In', self.zoomIn, 'Ctrl++')
        addMenuItem('Read', 'Zoom Out', self.zoomOut, 'Ctrl+-')

        addMenuItem('Read',
                    'General Options...',
                    mw.settingsManager.showSettingsDialog,
                    'Alt+1')

        addMenuItem('Read',
                    'Organizer...',
                    mw.readingManager.callIRSchedulerDialog,
                    'Alt+2')

        addMenuItem('Read',
                    'Create Shortcut...',
                    self.showAddCardQuickKeysDialog,
                    'Alt+3')

        addMenuItem('Read',
                    'Scheduler Options...',
                    mw.readingManager.callIRSchedulerOptionsDialog,
                    'Alt+4')

    def setDefaultDialogValues(self, keyModel):
        keyModel['deckName'] = None;
        keyModel['modelName'] = None;
        keyModel['fieldName'] = None;
        keyModel['ctrl'] = 'true';
        keyModel['shift'] = 'false';
        keyModel['alt'] = 'false';
        keyModel['keyName'] = None;
        keyModel['backgroundColor'] = 'yellow'
        keyModel['textColor'] = 'black'
        keyModel['showEditor'] = 'true';
        keyModel['showEditCurrent'] = 'false';
        keyModel['enabled'] = 'true';

    def showAddCardQuickKeysDialog(self):
        #set values from lastDialogQuickKey or use default
        if(len(self.lastDialogQuickKey.keys()) < 1):
            self.setDefaultDialogValues(self.lastDialogQuickKey);

        d = QDialog(mw)
        l = QVBoxLayout()
        l.setMargin(0)
        w = AnkiWebView()
        l.addWidget(w)
        #Add python object to take values back from javascript
        quickKeyModel = QuickKeyModel();
        w.page().mainFrame().addToJavaScriptWindowObject("quickKeyModel", quickKeyModel);
        #deck combo box
        deckComboBox = "<span style='font-weight:bold'>Deck: </span><select id='decks'>";
        allDecks = mw.col.decks.all();
        allDecks.sort(key=lambda dck: dck['name'], reverse=False)
        for deck in allDecks:
            isSelected = '';
            if(self.lastDialogQuickKey.get('deckName', None) == deck['name']):
                isSelected = 'selected';
            deckComboBox = deckComboBox + ("<option value='" + str(deck['id']) + "' " + isSelected + ">" + deck['name'] + "</option>");
        deckComboBox = deckComboBox + "</select>";
        #model combo box
        fieldChooserByModel = {};
        modelComboBox = "<span style='font-weight:bold'>Model: </span><select id='models'>";
        allModels = mw.col.models.all();
        allModels.sort(key=lambda mod: mod['name'], reverse=False)
        for model in allModels:
            isSelected = '';
            if(self.lastDialogQuickKey.get('modelName', None) == model['name']):
                isSelected = 'selected';
            modelComboBox = modelComboBox + ("<option value='" + str(model['id']) + "' " + isSelected + ">" + model['name'] + "</option>");
            listOfFields = model['flds'];
            fieldComboBox = "";
            for field in listOfFields:
                fieldComboBox = fieldComboBox + ("<option value='" + field['name'] + "'>" + field['name'] + "</option>");
            fieldChooserByModel[str(model['id'])] = fieldComboBox;
        modelComboBox = modelComboBox + "</select>";

        ctrl = '';
        if(self.lastDialogQuickKey.get('ctrl', 1) == 1): ctrl = 'checked';
        shift = '';
        if(self.lastDialogQuickKey.get('shift', 0) == 1): shift = 'checked';
        alt = '';
        if(self.lastDialogQuickKey.get('alt', 0) == 1): alt = 'checked';

        #Ctrl checkbox
        ctrlCheckbox = "<span style='font-weight:bold'>Ctrl: </span><input type='checkbox' id='ctrl' " + ctrl + " />";
        #Shift checkbox
        shiftCheckbox = "<span style='font-weight:bold'>Shift: </span><input type='checkbox' id='shift' " + shift + "/>";
        #Alt checkbox
        altCheckbox = "<span style='font-weight:bold'>Alt: </span><input type='checkbox' id='alt' " + alt + "/>";

        #shortcut key combo box
        keyComboBox = "<span style='font-weight:bold'>Key: </span><select id='keys'>";
        isSelected = '';
        for val in range(0,10):
            if(str(val) == str(self.lastDialogQuickKey.get('keyName','0'))): isSelected = 'selected';
            keyComboBox = keyComboBox + ("<option value='" + str(val) + "' " + isSelected + ">" + str(val) + "</option>");
            isSelected = '';
        for code in range(ord('a'), ord('z')+1):
            if(str(chr(code)) == str(self.lastDialogQuickKey.get('keyName','0'))): isSelected = 'selected';
            keyComboBox = keyComboBox + ("<option value='" + chr(code) + "' " + isSelected + ">" + chr(code) + "</option>");
            isSelected = '';
        keyComboBox = keyComboBox + "</select>";

        colorValue = self.lastDialogQuickKey.get('backgroundColor', 'yellow')
        backgroundColorField = "<span style='font-weight:bold'>Source highlighting color (background): </span><input type='text' id='backgroundColor' value='" + colorValue + "' />"

        colorValue = self.lastDialogQuickKey.get('textColor', 'black')
        textColorField = "<span style='font-weight:bold'>Source highlighting color (text): </span><input type='text' id='textColor' value='" + colorValue + "' />"

        #show editor checkbox
        doShowEditor = '';
        if(self.lastDialogQuickKey.get('showEditor', 1) == 1):
            doShowEditor = 'checked';
        showEditorCheckbox = "<span style='font-weight:bold'>Show Add Cards dialog?: </span><input type='checkbox' id='showEditor' " + doShowEditor + " />";
        #show current card editor checkbox
        doShowEditCurrent = '';
        if(self.lastDialogQuickKey.get('showEditCurrent', 0) == 1):
            doShowEditCurrent = 'checked';
        showEditCurrentCheckbox = "<span style='font-weight:bold'>Show Edit Current dialog?: </span><input type='checkbox' id='showEditCurrent' " + doShowEditCurrent + "/>";
        #remove shortcut checkbox
        doEnable = '';
        if(self.lastDialogQuickKey.get('enabled', 1) == 1):
            doEnable = 'checked';
        enabledCheckbox = "<span style='font-weight:bold'>Enable (uncheck to disable): </span><input type='checkbox' id='enabled' " + doEnable + " />";

        #javascript to populate field box based on selected model
        javascript = "var fieldsByModel = {};\n";
        for model in mw.col.models.all():
            listOfFields = model['flds'];
            javascript += "fieldsByModel['" + model['name'] + "'] = [";
            for field in listOfFields:
                javascript += "'" + re.escape(field['name']) + "',";
            javascript = javascript[:-1];
            javascript += "];\n";
        javascript += """
        function setFieldsForModel(mName) {
            var list = fieldsByModel[mName];
            var options = '';
            for(var i=0; i < list.length; i++) {
                var isSelected = '';
                if(list[i] == pasteToFieldValue) isSelected = 'selected';
                options += '<option value=\\'' + list[i] + '\\' ' + isSelected + '>' + list[i] + '</option>';
            }
            document.getElementById('fields').innerHTML = options;
        }
        """;
        javascript += "var pasteToFieldValue = '" + str(self.lastDialogQuickKey.get('fieldName', '')) + "';\n";
        html = "<html><head><script>" + javascript + "</script></head><body>";
        html += deckComboBox + "<p>";
        html += modelComboBox;
        html += "<p><span style='font-weight:bold'>Paste Text to Field: </span><select id='fields'>";
        html += fieldComboBox + "</select>";
        html += "<p><span style='font-weight:bold'>Key Combination:</span>&nbsp;&nbsp;" + ctrlCheckbox + "&nbsp;&nbsp;" + shiftCheckbox + "&nbsp;&nbsp;" + altCheckbox + "&nbsp;&nbsp;" + keyComboBox;
        #html += "<p>" + keyComboBox;
        html += "<p>" + backgroundColorField
        html += "<p>" + textColorField
        html += "<p>" + showEditorCheckbox;
        html += "<p>" + showEditCurrentCheckbox;
        html += "<p>" + enabledCheckbox;
        html += "</body></html>";
        #print html;
        w.stdHtml(html);
        #Dynamically add the javascript hook to call the setFieldsForModel function
        addHooksScript = """
        document.getElementById('models').onchange=function() {
            var sel = document.getElementById('models');
            setFieldsForModel(sel.options[sel.selectedIndex].text);
        };
        function getValues() {
            var sel = document.getElementById('decks');
            quickKeyModel.setDeck(sel.options[sel.selectedIndex].text);
            sel = document.getElementById('models');
            quickKeyModel.setModel(sel.options[sel.selectedIndex].text);
            sel = document.getElementById('fields');
            quickKeyModel.setField(sel.options[sel.selectedIndex].text);
            sel = document.getElementById('ctrl');
            quickKeyModel.setCtrl(sel.checked);
            sel = document.getElementById('shift');
            quickKeyModel.setShift(sel.checked);
            sel = document.getElementById('alt');
            quickKeyModel.setAlt(sel.checked);
            sel = document.getElementById('keys');
            quickKeyModel.setKey(sel.options[sel.selectedIndex].text);
            quickKeyModel.setBackgroundColor(document.getElementById('backgroundColor').value.trim());
            quickKeyModel.setTextColor(document.getElementById('textColor').value.trim());
            sel = document.getElementById('showEditor');
            quickKeyModel.setShowEditor(sel.checked);
            sel = document.getElementById('showEditCurrent');
            quickKeyModel.setShowEditCurrent(sel.checked);
            sel = document.getElementById('enabled');
            quickKeyModel.setEnabled(sel.checked);
        };
        //Set the fields for the selected model
	    var sel = document.getElementById('models');
        setFieldsForModel(sel.options[sel.selectedIndex].text);
        """
        w.eval(addHooksScript);
        bb = QDialogButtonBox(QDialogButtonBox.Close|QDialogButtonBox.Save)
        bb.connect(bb, SIGNAL("accepted()"), d, SLOT("accept()"))
        bb.connect(bb, SIGNAL("rejected()"), d, SLOT("reject()"))
        bb.setOrientation(Qt.Horizontal)
        l.addWidget(bb)
        d.setLayout(l)
        d.setWindowModality(Qt.WindowModal)
        d.resize(700, 500)
        choice = d.exec_();

        w.eval("getValues()");
        #move values to a map so they can be serialized to file later (Qt objects don't pickle well)
        keyModel = {};
        keyModel['deckName'] = quickKeyModel.deckName;
        keyModel['modelName'] = quickKeyModel.modelName;
        keyModel['fieldName'] = quickKeyModel.fieldName;

        #Ctrl + Shift + Alt + Key
        ctrl = 0;
        if(quickKeyModel.ctrl == 'true'): ctrl = 1;
        keyModel['ctrl'] = ctrl;
        shift = 0;
        if(quickKeyModel.shift == 'true'): shift = 1;
        keyModel['shift'] = shift;
        alt = 0;
        if(quickKeyModel.alt == 'true'): alt = 1;
        keyModel['alt'] = alt;
        keyModel['keyName'] = quickKeyModel.keyName;

        keyModel['backgroundColor'] = quickKeyModel.backgroundColor
        keyModel['textColor'] = quickKeyModel.textColor

        doShowEditor = 0;
        if(quickKeyModel.showEditor == 'true'):
            doShowEditor = 1;
        keyModel['showEditor'] = doShowEditor;
        doShowEditCurrent = 0;
        if(quickKeyModel.showEditCurrent == 'true'):
            doShowEditCurrent = 1;
        keyModel['showEditCurrent'] = doShowEditCurrent;
        keyModel['enabled'] = 1 if (quickKeyModel.enabled) else 0;
        #Save the last selected values in the dialog for later use
        self.lastDialogQuickKey = keyModel;
        #If SAVE chosen, then save the model as a new shortcut
        if(choice == 1):
            self.setQuickKey(keyModel);

    def setQuickKey(self, keyModel):
        keyCombo = ''
        if keyModel['ctrl'] == 1:
            keyCombo += "Ctrl+"
        if keyModel['shift'] == 1:
            keyCombo += "Shift+"
        if keyModel['alt'] == 1:
            keyCombo += "Alt+"
        keyCombo += keyModel['keyName']

        existingKeyModel = self.quickKeys.get(keyCombo, None)
        if keyModel['enabled'] == 1 and not existingKeyModel:
            callMe = lambda: self.quickAddCards(keyModel)
            menuText = 'Add Card [%s -> %s]' % (keyModel['modelName'],
                                                keyModel['deckName'])
            addMenuItem('Read', menuText, callMe, keyCombo)
            self.quickKeys[keyCombo] = keyModel
            self.savePluginData()

    def quickAddCards(self, quickKeyModel):
        hasSelection = 0;
        selectedText = '';
        #Copy text or html to clipboard if selected, else just use clipboard contents (user could hit Ctrl-C in a web browser instead)
        if(len(mw.web.selectedText()) > 0):
            hasSelection = 1;
            mw.web.triggerPageAction(QWebPage.Copy);
            clipboard = QApplication.clipboard();
            mimeData = clipboard.mimeData();
            selectedText = mimeData.html();

            mw.readingManager.highlightText(
                    quickKeyModel.get('backgroundColor', None),
                    quickKeyModel.get('textColor', None))

        #Create new note with selected model and deck
        new_model = mw.col.models.byName(quickKeyModel['modelName'])
        new_note = notes.Note(mw.col, new_model)
        setField(new_note, quickKeyModel['fieldName'], selectedText)

        #Add tags and copy source fields from source card, if applicable
        if(mw.reviewer.card):
            card = mw.reviewer.card
            cur_note = card.note()
            tags = cur_note.stringTags();
            new_note.setTagsFromStr(tags); #sets tags for the note, but still have to set them in the editor if show dialog (see below)

            #This is very specific to IR Model and should be generalized or moved elsewhere
            if(mw.reviewer.card.model()['name'] == IR_MODEL_NAME):
                for f in new_model['flds']:
                    if(SOURCE_FIELD_NAME == f['name']):
                        setField(new_note, SOURCE_FIELD_NAME, getField(cur_note, SOURCE_FIELD_NAME))

        #If shortcut said NOT to show AddCards dialog, then skip it.
        if(quickKeyModel['showEditor'] == 0):
            if(hasSelection == 1):
                new_note.model()['did'] = mw.col.decks.byName(quickKeyModel['deckName'])['id'];
                ret = new_note.dupeOrEmpty()
                if ret == 1:
                    showWarning(_(
                        "The first field is empty."),
                        help="AddItems#AddError")
                    return
                cards = mw.col.addNote(new_note)
                if not cards:
                    showWarning(_("""\
                        The input you have provided would make an empty \
                        question on all cards."""), help="AddItems")
                    return
                # stop anything playing
                clearAudioQueue()
                mw.col.autosave()
                tooltip(_("Added"), period=500)
        #Else show the add cards dialog
        else:
            self.acsCount += 1;
            if(quickKeyModel['showEditCurrent'] == 1): self.editCurrent = editcurrent.EditCurrent(mw);
            self.addCards = addcards.AddCards(mw)
            self.addCards.editor.setNote(new_note)
            if(new_note.stringTags() != None): self.addCards.editor.tags.setText(new_note.stringTags().strip()); #Not sure why doesn't get set automatically since note has associated tags, but ...
            self.addCards.modelChooser.models.setText(quickKeyModel['modelName'])
            self.addCards.deckChooser.deck.setText(quickKeyModel['deckName'])

    def resetZoom(self, state, *args):
        if state in ['deckBrowser', 'overview']:
            mw.web.setTextSizeMultiplier(self.settings['generalZoom'])
        elif (state == 'review' and
              self.previousState != 'review' and
              mw.reviewer.card and
              mw.reviewer.card.note().model()['name'] != IR_MODEL_NAME):
            mw.web.setTextSizeMultiplier(1)

        self.previousState = state

    def loadPluginData(self):
        self.settings = mw.settingsManager.settings
        if not self.controlsLoaded:
            self.addMenuItems()
            self.addShortcuts()
            self.addQuickKeys(self.settings['quickKeys'])
            self.controlsLoaded = True

        mw.moveToState = wrap(mw.moveToState, self.resetZoom, 'before')
        self.resetZoom('deckBrowser')

    def addQuickKeys(self, mapOfQuickKeys):
        for qkey in mapOfQuickKeys.keys():
            quickKey = mapOfQuickKeys.get(qkey, None);
            if(quickKey != None):
                #Set reasonable defaults for legacy shortcuts that did not previously support ctrl, shift, alt, showEditCurrent
                if(quickKey.get('ctrl', None) == None): quickKey['ctrl'] = 1;
                if(quickKey.get('shift', None) == None): quickKey['shift'] = 0;
                if(quickKey.get('alt', None) == None): quickKey['alt'] = 0;
                if(quickKey.get('showEditCurrent', None) == None): quickKey['showEditCurrent'] = 0;
                if(quickKey.get('showEditor', None) == None): quickKey['showEditor'] = 1;
                if(quickKey.get('enabled', None) == None): quickKey['enabled'] = 1;
                self.setQuickKey(quickKey);
            else: print "qkey not found: " + str(qkey);

    def savePluginData(self):
        quickKeysCopy = {}
        for qkey in self.quickKeys.keys():
            quickKey = self.quickKeys.get(qkey, None)
            if quickKey:
                quickKeysCopy[qkey] = quickKey.copy()

        lastDialogQuickKeyCopy = self.lastDialogQuickKey.copy()

        self.settings['quickKeys'] = quickKeysCopy
        self.settings['lastDialogQuickKey'] = lastDialogQuickKeyCopy

        mw.settingsManager.saveSettings()


class QuickKeyModel(QObject):
    deckName = '';
    modelName = '';
    fieldName = '';
    ctrl = True;
    shift = False;
    alt = False;
    keyName = '';
    backgroundColor = 'yellow'
    textColor = 'black'
    showEditor = True;
    enabled = True;
    @pyqtSlot(str)
    def setDeck(self, deck):
        self.deckName = deck;
    @pyqtSlot(str)
    def setModel(self, model):
        self.modelName = model;
    @pyqtSlot(str)
    def setField(self, field):
        self.fieldName = field;
    @pyqtSlot(str)
    def setCtrl(self, shouldShow):
        self.ctrl = shouldShow;
    @pyqtSlot(str)
    def setShift(self, shouldShow):
        self.shift = shouldShow;
    @pyqtSlot(str)
    def setAlt(self, shouldShow):
        self.alt = shouldShow;
    @pyqtSlot(str)
    def setKey(self, key):
        self.keyName = key;
    @pyqtSlot(str)
    def setBackgroundColor(self, color):
        self.backgroundColor = color
    @pyqtSlot(str)
    def setTextColor(self, color):
        self.textColor = color
    @pyqtSlot(str)
    def setShowEditor(self, shouldShow):
        self.showEditor = shouldShow;
    @pyqtSlot(str)
    def setShowEditCurrent(self, shouldShow):
        self.showEditCurrent = shouldShow;
    @pyqtSlot(str)
    def setEnabled(self, isEnabled):
        self.enabled = (isEnabled == 'true');

mw.viewManager = ViewManager()

addHook("profileLoaded", mw.viewManager.loadPluginData)
addHook('unloadProfile', mw.viewManager.savePluginData)


# Dangerous: We are monkey patching a method beginning with _
# Added these next two monkey patches (resetRequiredState and reviewState)
# to prevent reviewer from advancing to next card when using AddCards shortcuts.
def vsa_resetRequiredState(self, oldState, _old):
    #print "vsa_resetRequiredState: acsCount=" + str(self.viewManager.acsCount) + ", mw.reviewer.card=" + str(mw.reviewer.card) + ", and old state =" + oldState;
    specialHandling = False;
    if(self.viewManager.acsCount - self.viewManager.rrsCount == 1):
        specialHandling = True;
    self.viewManager.rrsCount = self.viewManager.acsCount;
    if (specialHandling and mw.reviewer.card):
        if oldState == "resetRequired":
            #print "vsa_resetRequiredState: Doing reset required with 'review'";
            return _old(self, 'review');
        else:
            #print "vsa_resetRequiredState: Doing reset required with old state: " + oldState;
            return _old(self, oldState);
        return;
    else:
        #print "vsa_resetRequiredState: Requisite conditions not met. Delegating to original resetRequiredState method.";
        return _old(self, oldState);

AnkiQt._resetRequiredState = wrap(AnkiQt._resetRequiredState, vsa_resetRequiredState, "around")


def saveScrollPosition(event):
    mw.viewManager.saveScrollPosition()

mw.web.wheelEvent = wrap(mw.web.wheelEvent, saveScrollPosition)
mw.web.mouseReleaseEvent = wrap(mw.web.mouseReleaseEvent,
                                saveScrollPosition,
                                'before')
