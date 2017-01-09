from aqt import mw, editcurrent, addcards
from aqt.reviewer import Reviewer
from aqt.webview import AnkiWebView
from aqt.utils import showInfo, tooltip
from anki import notes
from anki.hooks import wrap, addHook

import os
from stat import *
import pickle
import time
import random

from PyQt4.QtCore import *
from PyQt4 import QtCore
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebPage

IREAD_MODEL_NAME = 'IRead2'

TEXT_FIELD_NAME = 'Text'
SOURCE_FIELD_NAME = 'Source'
TITLE_FIELD_NAME = 'Title'

AFMT = "When do you want to see this card again?"


class IRead2(object):

    zoomAndScroll = {};
    highlightColor = 'yellow';
    doHighlightFont = 'false';
    ir2data = {'zoomAndScroll':zoomAndScroll,'highlightColor':highlightColor, 'doHighlightFont':'false'}
    setHighlightColorMenuItem = None;
    schedIROptions = 'pct,10,true,pct,60,true';
    schedSoonType = 'pct';
    schedSoonInt = 20;
    schedSoonRandom = True;
    schedLaterType = 'pct';
    schedLaterInt = 60;
    schedLaterRandom = True;

    def __init__(self, mw):
        self.mw = mw;

    #Invoked when profile loaded
    def loadPluginData(self):
        self.add_IRead_model(); #create the model if it doesn't exist

        #quick keys dialog
        if(self.setHighlightColorMenuItem != None):
            mw.disconnect(self.setHighlightColorMenuItem, SIGNAL("triggered()"), mw.IRead2.showSetHighlightColorDialog);
            self.setHighlightColorMenuItem.setEnabled(False);
            mw.form.menuEdit.removeAction(self.setHighlightColorMenuItem);
            del self.setHighlightColorMenuItem;
            mw.highlight.setEnabled(False);
            mw.disconnect(mw.highlight, SIGNAL("activated()"), mw.IRead2.showSetHighlightColorDialog);
        mw.highlight = QShortcut(QKeySequence("Alt+2"), mw);
        mw.connect(mw.highlight, SIGNAL("activated()"), mw.IRead2.showSetHighlightColorDialog);
        self.setHighlightColorMenuItem = QAction("[IRead2]: Set highlight color (Alt+2)", mw);
        mw.connect(self.setHighlightColorMenuItem, SIGNAL("triggered()"), mw.IRead2.showSetHighlightColorDialog);
        mw.form.menuEdit.addAction(self.setHighlightColorMenuItem);

        action = QAction("Incremental Reading Organizer", mw)
        mw.connect(action, SIGNAL("triggered()"), mw.IRead2.callIRSchedulerDialog)
        mw.form.menuTools.addAction(action)

        action = QAction("Incremental Reading Scheduler Options", mw)
        mw.connect(action, SIGNAL("triggered()"), mw.IRead2.callIRSchedulerOptionsDialog)
        mw.form.menuTools.addAction(action)

        # File to persist zoom and scroll data
        self.dataDir = self.mw.pm.profileFolder() + '/collection.media';
        self.dataFilename = self.dataDir + '/_IncrementalReadingExtension.dat';
        if(os.path.isfile(self.dataFilename)):
            f = open(self.dataFilename, "r")
            tmp = f.read()
            if(tmp):
                self.ir2data = pickle.loads(tmp);
                self.zoomAndScroll = self.ir2data['zoomAndScroll'];
                self.highlightColor = self.ir2data.get('highlightColor', 'yellow'); #default yellow
                self.doHighlightFont = self.ir2data.get('doHighlightFont', 'false'); #default false (highlight background)
                self.schedIROptions = self.ir2data.get('schedIROptions', 'pct,10,true,pct,50,true'); #default soon: pct,10,true (randomize); later: pct, 50, true (randomize)
                self.parseIROptions(self.schedIROptions);
            f.close();
        #Add a hook to adjust zoom and scroll when the web viewer is reset (ie. when editing is done. Typically only done when 'show question is pressed')
        #Has to be done here because we get errors if apply this hook to reset before everything is setup.
        addHook('reset',self.adjustZoomAndScroll);

    def savePluginData(self):
        #Capture zoom and scroll if exit directly from reviewer
        self.updateZoomAndScroll();
        # File to persist zoom and scroll data
        self.ir2data = {'zoomAndScroll':self.zoomAndScroll,'highlightColor':self.highlightColor,'doHighlightFont':self.doHighlightFont,'schedIROptions':self.schedIROptions}
        tmp = pickle.dumps(self.ir2data);
        f = open(self.dataFilename, "w")
        f.write(tmp)
        f.close();
        #touch the media folder to force sync
        st = os.stat(self.dataDir);
        atime = st[ST_ATIME] #access time
        new_mtime = time.time(); #new modification time
        os.utime(self.dataDir,(atime,new_mtime))

    def browseCard(self, cardId):
        pass

    def add_IRead_model(self):
        "Only adds model if no model with the same name is present"
        col = mw.col
        mm = col.models
        iread_model = mm.byName(IREAD_MODEL_NAME)
        if iread_model is None:
            iread_model = mm.new(IREAD_MODEL_NAME)
            # Field for title:
            model_field = mm.newField(TITLE_FIELD_NAME)
            mm.addField(iread_model, model_field)
            # Field for text:
            text_field = mm.newField(TEXT_FIELD_NAME)
            mm.addField(iread_model, text_field)
            # Field for source:
            source_field = mm.newField(SOURCE_FIELD_NAME)
            source_field['sticky'] = True
            mm.addField(iread_model, source_field)

            # Add template
            t = mm.newTemplate('IRead2 review')
            t['qfmt'] = "{{"+TEXT_FIELD_NAME+"}}"
            t['afmt'] = AFMT
            mm.addTemplate(iread_model, t)
            # Add model to collection:
            mm.add(iread_model)
            return iread_model
        else:
            fmap = mm.fieldMap(iread_model)
            title_ord, title_field = fmap[TITLE_FIELD_NAME]
            text_ord, text_field = fmap[TEXT_FIELD_NAME]
            source_ord, source_field = fmap[SOURCE_FIELD_NAME]
            source_field['sticky'] = True


    def extract(self):
        mw.viewManager.saveScrollPosition();
        #Copy text or html to clipboard and show (later will create card)
        if(len(mw.web.selectedText()) > 0): mw.web.triggerPageAction(QWebPage.Copy);
        clipboard = QApplication.clipboard();
        mimeData = clipboard.mimeData();
        #Highlight the text in the original document
        self.highlightSelectedText(self.highlightColor, self.doHighlightFont);

        card = mw.reviewer.card
        cur_note = card.note()
        col = mw.col
        deckName = col.decks.get(card.did)['name']
        model = col.models.byName(IREAD_MODEL_NAME)
        new_note = notes.Note(col, model)
        new_note.tags = cur_note.tags
        #setField(new_note, TITLE_FIELD_NAME, getField(cur_note, TITLE_FIELD_NAME))
        setField(new_note, TEXT_FIELD_NAME, mimeData.html())
        setField(new_note, SOURCE_FIELD_NAME, getField(cur_note, SOURCE_FIELD_NAME))
        self.editCurrent = editcurrent.EditCurrent(mw)

        self.addCards = addcards.AddCards(mw)
        self.addCards.editor.setNote(new_note)
        self.addCards.deckChooser.deck.setText(deckName)
        self.addCards.modelChooser.models.setText(IREAD_MODEL_NAME)

    def updateZoomAndScroll(self):
        mw.viewManager.saveScrollPosition();
        if(mw.reviewer.card):
            self.zoomAndScroll[mw.reviewer.card.id] = [mw.viewManager.textSizeMultiplier, mw.viewManager.verticalScrollPosition]

    #Added a hook to call this from 'reset'. Need to ensure it only affects IRead2 model.
    def adjustZoomAndScroll(self):
        if(mw.reviewer.card and mw.reviewer.card.model()['name'] == 'IRead2'):
            default = -1;
            vals = self.zoomAndScroll.get(mw.reviewer.card.id, default);
            if(vals != default):
                zoomFactor = vals[0];
                mw.viewManager.setZoomFactor(zoomFactor);
                scrollPosition = vals[1];
                mw.viewManager.setScrollPosition(scrollPosition);
            #Add python object to take values back from javascript
            pyCallback = IREJavaScriptCallback();
            self.mw.web.page().mainFrame().addToJavaScriptWindowObject("pyCallback", pyCallback);
            initJavaScript();
            mw.web.eval("highlightAllRanges()");

    def highlightSelectedText(self, color, doHighlightFont):
        if(self.mw.reviewer.card and self.mw.reviewer.card.model()['name'] == IREAD_MODEL_NAME): #Only highlight text if IRead2 model (need to make this general. Limited because of reference to 'Text' field)
            mw.viewManager.saveScrollPosition();
            self.updateZoomAndScroll();
            genId = time.time();
            genId *= 10;
            genId = int(genId);
            script = "markRange(" + str(genId) + ", '" + color + "', " + doHighlightFont + ");";
            script += "highlight('" + color + "', " + doHighlightFont + ");";
            mw.web.eval(script);
            curNote = self.mw.reviewer.card.note();
            curNote['Text'] = mw.web.page().mainFrame().toHtml();
            curNote.flush();
            mw.web.setHtml(curNote['Text']);
            self.adjustZoomAndScroll();

    def highlightText(self):
        self.highlightSelectedText(self.highlightColor, self.doHighlightFont);

    def htmlUpdated(self):
        #Called from javascript
        mw.viewManager.saveScrollPosition();
        self.updateZoomAndScroll();
        curNote = self.mw.reviewer.card.note();
        curNote['Text'] = mw.web.page().mainFrame().toHtml();
        curNote.flush();
        mw.web.setHtml(curNote['Text']);
        self.adjustZoomAndScroll();

    def showSetHighlightColorDialog(self):
        #Objective is a dialog to set highlight color used with 'h' key
        d = QDialog(self.mw)
        l = QVBoxLayout()
        l.setMargin(0)
        w = AnkiWebView()
        l.addWidget(w)
        #Add python object to take values back from javascript
        callback = IREHighlightColorCallback();
        w.page().mainFrame().addToJavaScriptWindowObject("callback", callback);
        getHighlightColorScript = """
        function getHighlightColor() {
            callback.setHighlightColor(document.getElementById('color').value.trim());
            if(document.getElementById('colorBackOrText').checked) {
                callback.setColorText('false');
            } else {
                callback.setColorText('true');
            }
        };
        """
        #color text box
        colorTextField = "<span style='font-weight:bold'>Source highlighting color (IRead2 model only): </span><input type='text' id='color' value='" + self.highlightColor + "' />";
        colorBackOrText = "<span style='font-weight:bold'>Apply color to: &nbsp;</span><input type='radio' id='colorBackOrText' name='colorBackOrText' value='false' checked='true' /> Background &nbsp;&nbsp;<input type='radio' name='colorBackOrText' value='true' /> Text<br />";
        html = "<html><head><script>" + getHighlightColorScript + "</script></head><body>";
        html += "<p>" + colorTextField;
        html += "<p>" + colorBackOrText;
        html += "</body></html>";
        w.stdHtml(html);
        bb = QDialogButtonBox(QDialogButtonBox.Close|QDialogButtonBox.Save)
        bb.connect(bb, SIGNAL("accepted()"), d, SLOT("accept()"))
        bb.connect(bb, SIGNAL("rejected()"), d, SLOT("reject()"))
        bb.setOrientation(QtCore.Qt.Horizontal);
        l.addWidget(bb)
        d.setLayout(l)
        d.setWindowModality(Qt.WindowModal)
        d.resize(500, 200)
        choice = d.exec_();
        if(choice == 1):
            w.eval("getHighlightColor()");

    def setHighlightColor(self, color):
        self.highlightColor = color;

    def setColorText(self, stringTrueIfText):
        self.doHighlightFont = stringTrueIfText;

    def callIRSchedulerOptionsDialog(self):
        d = QDialog(self.mw)
        l = QVBoxLayout()
        l.setMargin(0)
        w = AnkiWebView()
        l.addWidget(w)
        #Add python object to take values back from javascript
        callback = IROptionsCallback();
        w.page().mainFrame().addToJavaScriptWindowObject("callback", callback);
        getScript = """
        function updateIRSchedulerOptions() {
            //invoke the callback object
            var soonTypeCnt = document.getElementById('soonCntButton').checked;
            var laterTypeCnt = document.getElementById('laterCntButton').checked;
            var soonRandom = document.getElementById('soonRandom').checked;
            var laterRandom = document.getElementById('laterRandom').checked;
            var options = ''
            //Soon Button
            if(soonTypeCnt) options += 'cnt,';
            else options += 'pct,';
            options += document.getElementById('soonValue').value + ',';
            if(soonRandom) options += 'true,';
            else options += 'false,';
            //Later Button
            if(laterTypeCnt) options += 'cnt,';
            else options += 'pct,';
            options += document.getElementById('laterValue').value + ',';
            if(laterRandom) options += 'true';
            else options += 'false';
            callback.updateOptions(options);
        };
        """

        isCntChecked = '';
        isPctChecked = '';
        isRandomChecked = '';
        if(self.schedSoonType == 'cnt'):
            isCntChecked = 'checked';
            isPctChecked = '';
        else:
            isCntChecked = '';
            isPctChecked = 'checked';
        if(self.schedSoonRandom): isRandomChecked = 'checked';
        else: isRandomChecked = '';
        soonButtonConfig = "<span style='font-weight:bold'>Soon Button: &nbsp;</span>";
        soonButtonConfig += "<input type='radio' id='soonCntButton' name='soonCntOrPct' value='cnt' " + isCntChecked + " /> Position &nbsp;&nbsp;";
        soonButtonConfig += "<input type='radio' id='soonPctButton' name='soonCntOrPct' value='pct' " + isPctChecked + " /> Percent&nbsp;";
        soonButtonConfig += "<input type='text' size='5' id='soonValue' value='" + str(self.schedSoonInt) + "'/>";
        soonButtonConfig += "<span style='font-weight:bold'>&nbsp;&nbsp;&nbsp;&nbsp;Randomize?&nbsp;</span><input type='checkbox' id='soonRandom' " + isRandomChecked + " /><br/>";
        if(self.schedLaterType == 'cnt'):
            isCntChecked = 'checked';
            isPctChecked = '';
        else:
            isCntChecked = '';
            isPctChecked = 'checked';
        if(self.schedLaterRandom): isRandomChecked = 'checked';
        else: isRandomChecked = '';
        laterButtonConfig = "<span style='font-weight:bold'>Later Button: &nbsp;</span>";
        laterButtonConfig += "<input type='radio' id='laterCntButton' name='laterCntOrPct' value='cnt' " + isCntChecked + " /> Position &nbsp;&nbsp;";
        laterButtonConfig += "<input type='radio'  id='laterPctButton' name='laterCntOrPct' value='pct' " + isPctChecked + " /> Percent&nbsp;";
        laterButtonConfig += "<input type='text' size='5' id='laterValue' value='" + str(self.schedLaterInt) + "'/>";
        laterButtonConfig += "<span style='font-weight:bold'>&nbsp;&nbsp;&nbsp;&nbsp;Randomize?&nbsp;</span><input type='checkbox' id='laterRandom' " + isRandomChecked + " /><br/>";

        html = "<html><head><script>" + getScript + "</script></head><body>";
        html += "<p>" + soonButtonConfig;
        html += "<p>" + laterButtonConfig;
        html += "</body></html>";
        w.stdHtml(html);
        bb = QDialogButtonBox(QDialogButtonBox.Close|QDialogButtonBox.Save)
        bb.connect(bb, SIGNAL("accepted()"), d, SLOT("accept()"))
        bb.connect(bb, SIGNAL("rejected()"), d, SLOT("reject()"))
        bb.setOrientation(QtCore.Qt.Horizontal);
        l.addWidget(bb)
        d.setLayout(l)
        d.setWindowModality(Qt.WindowModal)
        d.resize(500, 140)
        choice = d.exec_();
        if(choice == 1):
            w.eval("updateIRSchedulerOptions()");

    def parseIROptions(self, optionsString):
        try:
            vals = optionsString.split(",");
            if(len(vals) > 0): self.schedSoonType = vals[0];
            if(len(vals) > 1): self.schedSoonInt = int(vals[1]);
            if(len(vals) > 2):
                self.schedSoonRandom = False;
                if(vals[2] == 'true'): self.schedSoonRandom = True;
            if(len(vals) > 3): self.schedLaterType = vals[3];
            if(len(vals) > 4): self.schedLaterInt = int(vals[4]);
            if(len(vals) > 5):
                self.schedLaterRandom = False;
                if(vals[5] == 'true'): self.schedLaterRandom = True;
            self.schedIROptions = optionsString;
        except:
            self.parseIROptions('pct,10,true,pct,50,true');

    #Needed this no-arg pass thru to be able to invoke dialog from menu
    def callIRSchedulerDialog(self):
        self.showIRSchedulerDialog(None);

    def showIRSchedulerDialog(self, currentCard):
        #Handle for dialog open without a current card from IRead2 model
        deckID = None;
        cardID = None;
        if(currentCard == None):
            deck = mw._selectedDeck();
            deckID = deck['id'];
        else:
            deckID = currentCard.did;
            cardID = currentCard.id;

        #Get the card data for the deck. Make sure it is an Incremental Reading deck (has IRead2 cards) before showing dialog
        cardDataList = self.getCardDataList(deckID, cardID);
        hasIRead2Cards = False;
        for cd in cardDataList:
            if(cd['title'] != 'No Title'): hasIRead2Cards = True;
        if(hasIRead2Cards == False):
            showInfo(_("Please select an Incremental Reading deck."))
            return;

        d = QDialog(self.mw)
        l = QVBoxLayout()
        l.setMargin(0)
        w = AnkiWebView()
        l.addWidget(w)
        #Add python object to take values back from javascript
        callback = IRSchedulerCallback();
        #callback.setCard(currentCard);
        w.page().mainFrame().addToJavaScriptWindowObject("callback", callback);
        #Script functions move up / move down / delete / open
        getIRSchedulerDialogScript = """
        var cardList = new Array();
        """
        index = 0;
        for cardData in cardDataList:
            index+=1;
            getIRSchedulerDialogScript += "card = new Object();";
            getIRSchedulerDialogScript += "card.id = " + str(cardData['id']) + ";";
            getIRSchedulerDialogScript += "card.title = '" + str(cardData['title']) + "';";
            getIRSchedulerDialogScript += "card.isCurrent = " + str(cardData['isCurrent']) + ";";
            getIRSchedulerDialogScript += "card.checkbox = document.createElement('input');";
            getIRSchedulerDialogScript += "card.checkbox.type = 'checkbox';";
            if(cardData['isCurrent'] == 'true'): getIRSchedulerDialogScript += "card.checkbox.setAttribute('checked', 'true');";
            getIRSchedulerDialogScript += "cardList[cardList.length] = card;";

        getIRSchedulerDialogScript += """
        function buildCardData() {
            var container = document.getElementById('cardList');
            container.innerHTML = '';
            var list = document.createElement('div');
            list.setAttribute('style','overflow:auto;');
            var table = document.createElement('table');
            list.appendChild(table);
            container.appendChild(list);
            var row;
            var col;
            var cardData;
            for(var i = 0; i < cardList.length; i++) {
                row = document.createElement('tr');
                row.setAttribute('id','row' + i);
                cardData = cardList[i];

                col = document.createElement('td');
                col.setAttribute('style','width:4em;');
                col.innerHTML = '' + i;
                row.appendChild(col);

                col = document.createElement('td');
                col.setAttribute('style','width:10em;');
                col.innerHTML = '' + cardData.id;
                row.appendChild(col);

                col = document.createElement('td');
                col.setAttribute('style','width:30em;');
                col.innerHTML = '' + cardData.title;
                row.appendChild(col);

                col = document.createElement('td');
                col.setAttribute('style','width:2em;');
                col.appendChild(cardData.checkbox);
                row.appendChild(col);

                table.appendChild(row);
            }
        }

        function reposition(origIndex, newIndex, isTopOfRange) {
            if(newIndex < 0 || newIndex > (cardList.length-1)) return -1;
            if(cardList[newIndex].checkbox.checked) return -1;

            if(isTopOfRange) {
                document.getElementById('newPos').value = newIndex;
            }
            var removedCards = cardList.splice(origIndex,1);
            cardList.splice(newIndex, 0, removedCards[0]);
            return newIndex;
        }

        function moveSelectedUp() {
            var topOfRange = -1;
            for(var i = 0; i < cardList.length; i++) {
                if(cardList[i].checkbox.checked) {
                    if(topOfRange == -1) topOfRange = i;
                    if(i == topOfRange) {
                        if(document.getElementById('anchor').checked) continue; //Don't move end of range if anchored.
                        else reposition(i, i - 1, true);
                    } else reposition(i, i - 1, false);
                }
            }
            buildCardData();
        }

        function moveSelectedDown() {
            var topOfRange = -1;
            var bottomOfRange = -1
            for(var i = 0; i < cardList.length; i++) {
                if(cardList[i].checkbox.checked) {
                    if(topOfRange == -1) topOfRange = i;
                    bottomOfRange = i;
                }
            }
            for(var i = cardList.length-1; i > -1; i--) {
                if(cardList[i].checkbox.checked) {
                    if(i == bottomOfRange && document.getElementById('anchor').checked) {
                        continue; //Don't move end of range if anchored.
                    }
                    if(i == topOfRange) reposition(i, i + 1, true);
                    else reposition(i, i + 1, false);
                }
            }
            buildCardData();
        }

        function selectAll() {
            for(var i = 0; i < cardList.length; i++) {
                cardList[i].checkbox.checked = true;
            }
        }

        function selectNone() {
            for(var i = 0; i < cardList.length; i++) {
                cardList[i].checkbox.checked = false;
            }
        }

        function directMove() {
            var newIndex = document.getElementById('newPos').value;
            var topOfRange = -1;
            origIndex = -1;
            for(var i = 0; i < cardList.length; i++) {
                if(cardList[i].checkbox.checked) {
                    if(topOfRange == -1) topOfRange = i;
                    if(origIndex == -1) {
                        origIndex = i;
                        sizeOfMove = (newIndex - origIndex);
                    }
                }
            }
            if(sizeOfMove < 0) {
                for(var i = 0; i < cardList.length; i++) {
                    if(cardList[i].checkbox.checked) {
                        if(i == topOfRange) reposition(i, i + sizeOfMove, true);
                        else reposition(i, i + sizeOfMove, false);
                    }
                }
            } else {
                for(var i = cardList.length-1; i > -1; i--) {
                    if(cardList[i].checkbox.checked) {
                        if(i == topOfRange) reposition(i, i + sizeOfMove, true);
                        else reposition(i, i + sizeOfMove, false);
                    }
                }
            }
            buildCardData();
        }

        function updatePositions() {
            var cids = new Array();
            for(var i=0; i < cardList.length; i++) {
                cids[cids.length] = parseInt(cardList[i].id);
            }
            callback.updatePositions(cids);
        };
        """;

        #Incremental Reading list as a list of nested <div> tags (like a table, but more flexible)
        #position,title,series id, sequence number,card id (hidden)
        newPosField = "<span style='font-weight:bold'>Card Position: </span><input type='text' id='newPos' size='5' value='0' />&nbsp;<span style='font-weight:bold'>of " + str(len(cardDataList)) + "</span>&nbsp;&nbsp;";
        newPosField += "<input type='button' value='Apply' onclick='directMove()' />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='font-weight:bold'>Pin Top/Bottom? </span><input type='checkbox' id='anchor'/>";

        upDownButtons = "<input type='button' value='Move Up' onclick='moveSelectedUp()'/><input type='button' value='Move Down' onclick='moveSelectedDown()'/>";
        upDownButtons += "<input type='button' value='Select All' onclick='selectAll()'/><input type='button' value='Select None' onclick='selectNone()'/>";

        html = "<html><head><script>" + getIRSchedulerDialogScript + "</script></head><body onLoad='buildCardData()'>";
        html += "<p>" + newPosField;
        html += "<p>" + upDownButtons;
        html += "<div id='cardList'></div>";
        html += "</body></html>";
        w.stdHtml(html);
        bb = QDialogButtonBox(QDialogButtonBox.Close|QDialogButtonBox.Save)
        bb.connect(bb, SIGNAL("accepted()"), d, SLOT("accept()"))
        bb.connect(bb, SIGNAL("rejected()"), d, SLOT("reject()"))
        bb.setOrientation(QtCore.Qt.Horizontal);
        l.addWidget(bb)
        d.setLayout(l)
        d.setWindowModality(Qt.WindowModal)
        d.resize(500, 500)
        choice = d.exec_();
        if(choice == 1):
            w.eval("updatePositions()");
        else:
            if(currentCard != None): self.repositionCard(currentCard, -1);

    def scheduleCard(self, answeredCard, ease):
        cnt = -1;
        pct = -1;

        if(ease == 1): #soon
            if(self.schedSoonType == 'pct'):
                if(self.schedSoonRandom == True): pct = float(random.randint(1, self.schedSoonInt))/float(100);
                else: pct = float(self.schedSoonInt)/float(100);
            else:
                cnt = self.schedSoonInt;
                if(self.schedSoonRandom == True): cnt = random.randint(1, self.schedSoonInt);
        elif(ease == 2):
            if(self.schedSoonType == 'pct'):
                if(self.schedLaterRandom == True): pct = float(random.randint(self.schedSoonInt, self.schedLaterInt))/float(100);
                else: pct = float(self.schedLaterInt)/float(100);
            else:
                cnt = self.schedLaterInt;
                if(self.schedLaterRandom == True): cnt = random.randint(self.schedSoonInt, self.schedLaterInt);
        elif(ease == 3):
            mw.IRead2.showIRSchedulerDialog(answeredCard);
            return;
        elif(ease == 4):
            pct = 1;
        if(pct > -1):
            cds = mw.IRead2.getIRCards(answeredCard);
            pos = int(len(cds) * pct);
            tooltip(_("Card moved (" + str(int(100*pct)) + "%) to position:  " + str(pos)), period=1500);
        elif(cnt > -1):
            pos = cnt;
            tooltip(_("Card moved to position:  " + str(pos)), period=1500);
        else:
            pos = 5; #reasonable default
            tooltip(_("Card moved by default to position:  " + str(pos)), period=1500);
        self.repositionCard(answeredCard, pos);

    def repositionCard(self, card, pos):

        #Clear card's current status (put in NEW queue)
        cds = [];
        cds.append(card.id);
        mw.col.sched.forgetCards(cds);

        if(pos < 0):
            return; #If opened dialog and chose not to specify a position, card ends up at end of NEW queue by default.

        #Put card in new position
        cds = self.getIRCards(card);
        index = 0;
        newCardOrder = [];
        for cid in cds:
            #print "OLD Card Order (" + str(card.id) + "): " + str(cid);
            if(cid != card.id):
                if(index == pos):
                    #print "At Index (" + str(cid) + " != " + str(card.id) + "): Repositioning card to " + str(index);
                    newCardOrder.append(card.id);
                    index+=1;
                    newCardOrder.append(cid);
                else:
                    newCardOrder.append(cid);
            else:
                if(index == pos):
                    #print "Repositioning card to " + str(index);
                    newCardOrder.append(card.id);
            index+=1;
        #for cid in newCardOrder:
        #    print "New Card Order (" + str(card.id) + "): " + str(cid);
        mw.col.sched.sortCards(newCardOrder);

    def repositionCards(self, cids):
        #Clear card's current status (put in NEW queue)
        mw.col.sched.forgetCards(cids);
        #Reorder to match the list (cids) passed in
        mw.col.sched.sortCards(cids);

    def getIRCards(self, card):
        cds = [];
        for id, nid in mw.col.db.execute(
                #"select id, nid from cards where type = 0 and did = " + str(card.did)):
                "select id, nid from cards where did = " + str(card.did)):
                    cds.append(id);
        return cds;

    def getCardDataList(self, deckID, cardID):
        cardDataList = [];
        note = None;
        for id, nid in mw.col.db.execute(
            #"select id, nid from cards where type = 0 and did = " + str(card.did)):
            "select id, nid from cards where did = " + str(deckID)):
                cardData = {};
                cardData['id'] = id;
                cardData['nid'] = nid;
                note = mw.col.getNote(nid);

                if(note.model()['name'] == 'IRead2'):
                    cardData['title'] = (note['Title'][:64].encode('ascii',
                        errors='xmlcharrefreplace')).encode('string_escape')
                else: cardData['title'] = 'No Title';
                #cardData['title'] = 'No Title';

                if(cardID == id): cardData['isCurrent'] = 'true';
                else: cardData['isCurrent'] = 'false';

                cardDataList.append(cardData);
        return cardDataList;

class IROptionsCallback(QtCore.QObject):
    @QtCore.pyqtSlot(str)
    def updateOptions(self, options):
        mw.IRead2.parseIROptions(options);

class IRSchedulerCallback(QtCore.QObject):
    @QtCore.pyqtSlot(str)
    def updatePositions(self, ids):
        cids = ids.split(",");
        mw.IRead2.repositionCards(cids);

class IREJavaScriptCallback(QtCore.QObject):
    @QtCore.pyqtSlot(str)
    def htmlUpdated(self, context):
        mw.IRead2.htmlUpdated();

class IREHighlightColorCallback(QtCore.QObject):
    @QtCore.pyqtSlot(str)
    def setHighlightColor(self, string):
        mw.IRead2.setHighlightColor(string);
    @QtCore.pyqtSlot(str)
    def setColorText(self, string):
        mw.IRead2.setColorText(string);

def setField(note, name, content):
    ord = mw.col.models.fieldMap(note.model())[name][0]
    note.fields[ord] = content
    return note

def getField(note, name):
    ord = mw.col.models.fieldMap(note.model())[name][0]
    return note.fields[ord]

def initJavaScript():
    #Highlight the text selected
    javaScript = """
    function makeEditableAndHighlight(colour, hiliteFont) {
        var range, sel = window.getSelection();
        if (sel.rangeCount && sel.getRangeAt) {
            range = sel.getRangeAt(0);
        }
        document.designMode = "on";
        if (range) {
            sel.removeAllRanges();
            sel.addRange(range);
        }
        // Use HiliteColor since some browsers apply BackColor to the whole block
        // Some wierdness with the hiliteFont variable. Sometimes a true boolean, other times a string. Check both. (FIX ME)
        if(hiliteFont == true || hiliteFont == 'true') {
            document.execCommand("foreColor", false, colour);
        } else {
            if (!document.execCommand("HiliteColor", false, colour)) {
                document.execCommand("BackColor", false, colour);
            }
        }
        document.designMode = "off";
        sel.removeAllRanges();
    }

    function highlight(colour, hiliteFont) {
        if (window.getSelection) {
            makeEditableAndHighlight(colour, hiliteFont);
            // IE9 and non-IE
            //try {
            //    if (!document.execCommand("BackColor", false, colour)) {
            //        makeEditableAndHighlight(colour, hiliteFont);
            //    }
            //} catch (ex) {
           //     makeEditableAndHighlight(colour)
            //}
        }
    }

    function unhighlight(identifier, hiliteFont) {
        var startNode, endNode;
        startNode = document.getElementById('s' + identifier);
        endNode = document.getElementById('e' + identifier);
        if(startNode) {
            range = document.createRange();
            range.setStartAfter(startNode);
            range.setEndBefore(endNode);
            sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            if(hiliteFont) highlight('black', hiliteFont);
            else highlight('white', hiliteFont);
            startNode.parentNode.removeChild(startNode);
            endNode.parentNode.removeChild(endNode);
            pyCallback.htmlUpdated('');
        }
    }

    function markRange(identifier, color, hiliteFont) {
        var range, sel = window.getSelection();
        if(sel.rangeCount && sel.getRangeAt) {
            range = sel.getRangeAt(0);
            var startNode = document.createElement('span');
            startNode.setAttribute('id', ('s' + identifier));
            startNode.setAttribute('hiclr', color);
            startNode.setAttribute('hifont', hiliteFont);
            range.insertNode(startNode);
            var endNode = document.createElement('span');
            endNode.setAttribute('id', ('e' + identifier));
            endNode.setAttribute('style', 'font-size:xx-small');
            editHighlightLink = document.createElement('a');
            editHighlightLink.setAttribute('href','javascript:');
            var tmp = ('unhighlight(' + identifier + ', ' + hiliteFont + '); return false;');
            editHighlightLink.setAttribute('onclick', tmp);
            sub = document.createElement('sub');
            sub.appendChild(document.createTextNode('#'));
            editHighlightLink.appendChild(sub);
            endNode.appendChild(editHighlightLink);
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
        if(startNode && endNode) {
            range = document.createRange();
            range.setStartAfter(startNode);
            range.setEndBefore(endNode);
            sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            return startNode.getAttribute('hiclr');
        } else return 'white';
    }

    function highlightAllRanges() {
        var startNodesXPathResult = document.evaluate('//*[@hiclr]', document, null, XPathResult.ANY_TYPE, null);
        var sNodes = new Array();
        var startNode = startNodesXPathResult.iterateNext();
        while(startNode) {
            sNodes.push(startNode);
            startNode = startNodesXPathResult.iterateNext();
        }
        var id;
        for(var i=0; i < sNodes.length; i++) {
            startNode = sNodes[i];
            id = startNode.id.substring(1);
            selectMarkedRange(id);
            highlight(startNode.getAttribute('hiclr'), startNode.getAttribute('hifont'));
        }
    }
    """;
    mw.web.eval(javaScript);


# this will be called after Reviewer._keyHandler
def my_reviewer_keyHandler(self, evt):
    key = unicode(evt.text())
    if key == "x": # e[X]tract
        if self.card.note().model()['name'] == IREAD_MODEL_NAME:
            mw.IRead2.extract()
    elif key == "h": # [H]ighlight
        if self.card.note().model()['name'] == IREAD_MODEL_NAME:
            mw.IRead2.highlightText();

mw.IRead2 = IRead2(mw)
addHook('profileLoaded', mw.IRead2.loadPluginData)
addHook('unloadProfile', mw.IRead2.savePluginData)
addHook('showQuestion', mw.IRead2.adjustZoomAndScroll)
addHook('showAnswer', mw.IRead2.updateZoomAndScroll)
addHook('reviewCleanup', mw.IRead2.updateZoomAndScroll);
addHook('highlightText', mw.IRead2.highlightSelectedText);
#mw.web.setHtml = wrap(mw.web.setHtml, mw.viewManager.restoreScrollPosition());
# Dangerous: We are monkey patching a method beginning with _
Reviewer._keyHandler = wrap(Reviewer._keyHandler, my_reviewer_keyHandler)

#Below monkey patching done to support Incremental Reading scheduler (change button labels and behaviors)
def my_reviewer_answerButtonList(self, _old):
    answeredCard = self.card;
    #Only manipulate buttons if Incremental Reading deck
    if(answeredCard.model()['name'] == 'IRead2'):
        l = ((1, _("Soon")),)
        cnt = self.mw.col.sched.answerButtons(self.card)
        if cnt == 2:
            return l + ((2, _("Later")),)
        elif cnt == 3:
            return l + ((2, _("Later")), (3, _("Custom")))
        else:
            return l + ((2, _("Later")), (3, _("MuchLater")), (4, _("Custom")))
    else:
        return _old(self);

def my_reviewer_buttonTime(self, i, _old):
    answeredCard = self.card;
    #Only manipulate button time if Incremental Reading deck
    if(answeredCard.model()['name'] == 'IRead2'): return "<div class=spacer></div>";
    else: return _old(self, i);

def my_reviewer_answerCard(self, ease, _old):
    #Get the card before scheduler kicks in, else you are looking at a different card or NONE (which gives error)
    answeredCard = self.card;

    #Always do the regular Anki scheduling logic (for non-Incremental Reading decks, and also because UI behavior is assured
    #to be consistent this way. Below code only manipulates the database, not the UI.)
    _old(self, ease);

    #Only manipulate the deck if this is an Incremental Reading deck
    if(answeredCard.model()['name'] == 'IRead2'):
        #print "Ease: " + str(ease);
        #print "Card id: " + str(answeredCard.id);
        mw.IRead2.scheduleCard(answeredCard, ease);

Reviewer._answerCard = wrap(Reviewer._answerCard, my_reviewer_answerCard, "around")
Reviewer._answerButtonList = wrap(Reviewer._answerButtonList, my_reviewer_answerButtonList, "around")
Reviewer._buttonTime = wrap(Reviewer._buttonTime, my_reviewer_buttonTime, "around")
