# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import time
import random
import re

from BeautifulSoup import BeautifulSoup
from PyQt4.QtCore import QObject, QPoint, Qt, SIGNAL, SLOT, pyqtSlot
from PyQt4.QtGui import (QApplication, QDialog, QDialogButtonBox, QHBoxLayout,
                         QLabel, QLineEdit, QVBoxLayout)
from PyQt4.QtWebKit import QWebPage
from anki.notes import Note
from anki.hooks import addHook, wrap
from aqt import mw
from aqt.editcurrent import EditCurrent
from aqt.addcards import AddCards
from aqt.reviewer import Reviewer
from aqt.utils import showInfo, tooltip
from aqt.webview import AnkiWebView

from ir.settings import SettingsManager
from ir.util import getField, setField

IR_MODEL_NAME = 'IR3'
TEXT_FIELD_NAME = 'Text'
SOURCE_FIELD_NAME = 'Source'
TITLE_FIELD_NAME = 'Title'

AFMT = "When do you want to see this card again?"


class ReadingManager():
    def loadPluginData(self):
        self.add_IRead_model()
        mw.settingsManager = SettingsManager()
        self.settings = mw.settingsManager.settings
        addHook('reset', mw.readingManager.adjustZoomAndScroll)

    def savePluginData(self):
        mw.settingsManager.saveSettings()

    def add_IRead_model(self):
        "Only adds model if no model with the same name is present"
        col = mw.col
        mm = col.models
        iread_model = mm.byName(IR_MODEL_NAME)
        if iread_model is None:
            iread_model = mm.new(IR_MODEL_NAME)
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
            t = mm.newTemplate('IR Card')
            t['qfmt'] = '<div class="ir-text">{{%s}}</div>' % (TEXT_FIELD_NAME)
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
        if mw.web.selectedText():
            mw.web.triggerPageAction(QWebPage.Copy)

        mimeData = QApplication.clipboard().mimeData()

        if self.settings['extractPlainText']:
            text = mimeData.text()
        else:
            text = mimeData.html()

        self.highlightText(self.settings['highlightColor'],
                           self.settings['textColor'])

        currentCard = mw.reviewer.card
        currentNote = currentCard.note()
        model = mw.col.models.byName(IR_MODEL_NAME)
        newNote = Note(mw.col, model)
        newNote.tags = currentNote.tags

        setField(newNote, TEXT_FIELD_NAME, text)
        setField(newNote,
                 SOURCE_FIELD_NAME,
                 getField(currentNote, SOURCE_FIELD_NAME))

        if self.settings['editSourceNote']:
            EditCurrent(mw)

        if self.settings['editExtractedNote']:
            addCards = AddCards(mw)
            addCards.editor.setNote(newNote)
            deckName = mw.col.decks.get(currentCard.did)['name']
            addCards.deckChooser.deck.setText(deckName)
            addCards.modelChooser.models.setText(IR_MODEL_NAME)
        else:
            setField(newNote, TITLE_FIELD_NAME, self.getNewTitle())
            newNote.model()['did'] = currentCard.did
            mw.col.addNote(newNote)

    def getNewTitle(self):
        dialog = QDialog(mw)
        dialog.setWindowTitle('Extract Text')
        titleLabel = QLabel('Title')
        titleEditBox = QLineEdit()
        titleEditBox.setFixedWidth(300)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        buttonBox.connect(buttonBox,
                          SIGNAL('accepted()'),
                          dialog,
                          SLOT('accept()'))
        layout = QHBoxLayout()
        layout.addWidget(titleLabel)
        layout.addWidget(titleEditBox)
        layout.addWidget(buttonBox)
        dialog.setLayout(layout)
        dialog.exec_()
        return titleEditBox.text()

    def adjustZoomAndScroll(self):
        if mw.reviewer.card and mw.reviewer.card.model()['name'] == IR_MODEL_NAME:
            cardID = str(mw.reviewer.card.id)

            if cardID not in self.settings['zoom']:
                self.settings['zoom'][cardID] = 1

            if cardID not in self.settings['scroll']:
                self.settings['scroll'][cardID] = 0

            mw.web.setTextSizeMultiplier(
                    self.settings['zoom'][cardID])

            position = self.settings['scroll'][cardID]
            mw.web.page().mainFrame().setScrollPosition(QPoint(0, position))

            self.highlightAllRanges()

    def highlightAllRanges(self):
        # Add python object to take values back from javascript
        pyCallback = IREJavaScriptCallback()
        mw.web.page().mainFrame().addToJavaScriptWindowObject("pyCallback", pyCallback)
        initJavaScript()
        mw.web.eval("highlightAllRanges()")

    def highlightText(self, backgroundColor=None, textColor=None):
        if not backgroundColor:
            backgroundColor = self.settings['highlightColor']
        if not textColor:
            textColor = self.settings['textColor']

        # No obvious/easy way to do this with BeautifulSoup
        def removeOuterDiv(html):
            withoutOpenDiv = re.sub('^<div[^>]+>', '', unicode(html))
            withoutCloseDiv = re.sub('</div>$', '', withoutOpenDiv)
            return withoutCloseDiv

        currentCard = mw.reviewer.card
        currentModelName = currentCard.model()['name']
        currentNote = currentCard.note()

        # Need to make this general
        # Limited because of reference to 'Text' field
        if currentCard and currentModelName == IR_MODEL_NAME:
            identifier = str(int(time.time() * 10))
            script = "markRange('%s', '%s', '%s');" % (identifier,
                                                       backgroundColor,
                                                       textColor)
            script += "highlight('%s', '%s');" % (backgroundColor, textColor)
            mw.web.eval(script)

            page = mw.web.page().mainFrame().toHtml()
            soup = BeautifulSoup(page)
            irTextDiv = soup.find('div', {'class': 'ir-text'})

            if irTextDiv:
                withoutDiv = removeOuterDiv(irTextDiv)
                currentNote['Text'] = unicode(withoutDiv)
                currentNote.flush()
                self.adjustZoomAndScroll()

    def htmlUpdated(self):
        #Called from javascript
        curNote = mw.reviewer.card.note();
        curNote['Text'] = mw.web.page().mainFrame().toHtml();
        curNote.flush();
        mw.web.setHtml(curNote['Text']);
        self.adjustZoomAndScroll();

    def callIRSchedulerOptionsDialog(self):
        d = QDialog(mw)
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
        if(self.settings['schedSoonType'] == 'cnt'):
            isCntChecked = 'checked';
            isPctChecked = '';
        else:
            isCntChecked = '';
            isPctChecked = 'checked';
        if(self.settings['schedSoonRandom']): isRandomChecked = 'checked';
        else: isRandomChecked = '';
        soonButtonConfig = "<span style='font-weight:bold'>Soon Button: &nbsp;</span>";
        soonButtonConfig += "<input type='radio' id='soonCntButton' name='soonCntOrPct' value='cnt' " + isCntChecked + " /> Position &nbsp;&nbsp;";
        soonButtonConfig += "<input type='radio' id='soonPctButton' name='soonCntOrPct' value='pct' " + isPctChecked + " /> Percent&nbsp;";
        soonButtonConfig += "<input type='text' size='5' id='soonValue' value='" + str(self.settings['schedSoonInt']) + "'/>";
        soonButtonConfig += "<span style='font-weight:bold'>&nbsp;&nbsp;&nbsp;&nbsp;Randomize?&nbsp;</span><input type='checkbox' id='soonRandom' " + isRandomChecked + " /><br/>";
        if(self.settings['schedLaterType'] == 'cnt'):
            isCntChecked = 'checked';
            isPctChecked = '';
        else:
            isCntChecked = '';
            isPctChecked = 'checked';
        if(self.settings['schedLaterRandom']): isRandomChecked = 'checked';
        else: isRandomChecked = '';
        laterButtonConfig = "<span style='font-weight:bold'>Later Button: &nbsp;</span>";
        laterButtonConfig += "<input type='radio' id='laterCntButton' name='laterCntOrPct' value='cnt' " + isCntChecked + " /> Position &nbsp;&nbsp;";
        laterButtonConfig += "<input type='radio'  id='laterPctButton' name='laterCntOrPct' value='pct' " + isPctChecked + " /> Percent&nbsp;";
        laterButtonConfig += "<input type='text' size='5' id='laterValue' value='" + str(self.settings['schedLaterInt']) + "'/>";
        laterButtonConfig += "<span style='font-weight:bold'>&nbsp;&nbsp;&nbsp;&nbsp;Randomize?&nbsp;</span><input type='checkbox' id='laterRandom' " + isRandomChecked + " /><br/>";

        html = "<html><head><script>" + getScript + "</script></head><body>";
        html += "<p>" + soonButtonConfig;
        html += "<p>" + laterButtonConfig;
        html += "</body></html>";
        w.stdHtml(html);
        bb = QDialogButtonBox(QDialogButtonBox.Close|QDialogButtonBox.Save)
        bb.connect(bb, SIGNAL("accepted()"), d, SLOT("accept()"))
        bb.connect(bb, SIGNAL("rejected()"), d, SLOT("reject()"))
        bb.setOrientation(Qt.Horizontal)
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
            if(len(vals) > 0): self.settings['schedSoonType'] = vals[0];
            if(len(vals) > 1): self.settings['schedSoonInt'] = int(vals[1]);
            if(len(vals) > 2):
                self.settings['schedSoonRandom'] = False;
                if(vals[2] == 'true'): self.settings['schedSoonRandom'] = True;
            if(len(vals) > 3): self.settings['schedLaterType'] = vals[3];
            if(len(vals) > 4): self.settings['schedLaterInt'] = int(vals[4]);
            if(len(vals) > 5):
                self.settings['schedLaterRandom'] = False;
                if(vals[5] == 'true'): self.settings['schedLaterRandom'] = True;
        except:
            self.parseIROptions('pct,10,true,pct,50,true');

    #Needed this no-arg pass thru to be able to invoke dialog from menu
    def callIRSchedulerDialog(self):
        self.showIRSchedulerDialog(None);

    def showIRSchedulerDialog(self, currentCard):
        #Handle for dialog open without a current card from IR model
        deckID = None;
        cardID = None;
        if(currentCard == None):
            deck = mw._selectedDeck();
            deckID = deck['id'];
        else:
            deckID = currentCard.did;
            cardID = currentCard.id;

        #Get the card data for the deck. Make sure it is an Incremental Reading deck (has IR cards) before showing dialog
        cardDataList = self.getCardDataList(deckID, cardID);
        hasIRCards = False;
        for cd in cardDataList:
            if(cd['title'] != 'No Title'): hasIRCards = True;
        if(hasIRCards == False):
            showInfo(_("Please select an Incremental Reading deck."))
            return;

        d = QDialog(mw)
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
        bb.setOrientation(Qt.Horizontal)
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
            if(self.settings['schedSoonType'] == 'pct'):
                if(self.settings['schedSoonRandom'] == True): pct = float(random.randint(1, self.settings['schedSoonInt']))/float(100);
                else: pct = float(self.settings['schedSoonInt'])/float(100);
            else:
                cnt = self.settings['schedSoonInt'];
                if(self.settings['schedSoonRandom'] == True): cnt = random.randint(1, self.settings['schedSoonInt']);
        elif(ease == 2):
            if(self.settings['schedSoonType'] == 'pct'):
                if(self.settings['schedLaterRandom'] == True): pct = float(random.randint(self.settings['schedSoonInt'], self.settings['schedLaterInt']))/float(100);
                else: pct = float(self.settings['schedLaterInt'])/float(100);
            else:
                cnt = self.settings['schedLaterInt'];
                if(self.settings['schedLaterRandom'] == True): cnt = random.randint(self.settings['schedSoonInt'], self.settings['schedLaterInt']);
        elif(ease == 3):
            mw.readingManager.showIRSchedulerDialog(answeredCard);
            return;
        elif(ease == 4):
            pct = 1;
        if(pct > -1):
            cds = mw.readingManager.getIRCards(answeredCard);
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

                if(note.model()['name'] == IR_MODEL_NAME):
                    cardData['title'] = (note['Title'][:64].encode('ascii',
                        errors='xmlcharrefreplace')).encode('string_escape')
                else: cardData['title'] = 'No Title';
                #cardData['title'] = 'No Title';

                if(cardID == id): cardData['isCurrent'] = 'true';
                else: cardData['isCurrent'] = 'false';

                cardDataList.append(cardData);
        return cardDataList;

class IROptionsCallback(QObject):
    @pyqtSlot(str)
    def updateOptions(self, options):
        mw.readingManager.parseIROptions(options);

class IRSchedulerCallback(QObject):
    @pyqtSlot(str)
    def updatePositions(self, ids):
        cids = ids.split(",");
        mw.readingManager.repositionCards(cids);

class IREJavaScriptCallback(QObject):
    @pyqtSlot(str)
    def htmlUpdated(self, context):
        mw.readingManager.htmlUpdated();


def initJavaScript():
    javaScript = """
    function highlight(backgroundColor, textColor) {
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
            document.execCommand("hiliteColor", false, backgroundColor);

            document.designMode = "off";
            sel.removeAllRanges();
        }
    }

    function unhighlight(identifier) {
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
            highlight('white', 'black');
            startNode.parentNode.removeChild(startNode);
            endNode.parentNode.removeChild(endNode);
            pyCallback.htmlUpdated('');
        }
    }

    function markRange(identifier, backgroundColor, textColor) {
        var range, sel = window.getSelection();
        if(sel.rangeCount && sel.getRangeAt) {
            range = sel.getRangeAt(0);
            var startNode = document.createElement('span');
            startNode.setAttribute('id', ('s' + identifier));
            startNode.setAttribute('ir-bg-color', backgroundColor);
            startNode.setAttribute('ir-text-color', textColor);
            range.insertNode(startNode);
            var endNode = document.createElement('span');
            endNode.setAttribute('id', ('e' + identifier));
            endNode.setAttribute('style', 'font-size:xx-small');
            editHighlightLink = document.createElement('a');
            editHighlightLink.setAttribute('href','javascript:');
            var tmp = ('unhighlight(' + identifier + '); return false;');
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
        }
    }

    function highlightAllRanges() {
        var startNodesXPathResult = document.evaluate('//*[@ir-bg-color]', document, null, XPathResult.ANY_TYPE, null);
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
            highlight(startNode.getAttribute('ir-bg-color'),
                      startNode.getAttribute('ir-text-color'))
        }
    }
    """
    mw.web.eval(javaScript)


# this will be called after Reviewer._keyHandler
def my_reviewer_keyHandler(self, evt):
    key = unicode(evt.text())
    if key == "x": # e[X]tract
        if self.card.note().model()['name'] == IR_MODEL_NAME:
            mw.readingManager.extract()
    elif key == "h": # [H]ighlight
        if self.card.note().model()['name'] == IR_MODEL_NAME:
            mw.readingManager.highlightText();

mw.readingManager = ReadingManager()

addHook('profileLoaded', mw.readingManager.loadPluginData)
addHook('unloadProfile', mw.readingManager.savePluginData)
addHook('showQuestion', mw.readingManager.adjustZoomAndScroll)

# Dangerous: We are monkey patching a method beginning with _
Reviewer._keyHandler = wrap(Reviewer._keyHandler, my_reviewer_keyHandler)

#Below monkey patching done to support Incremental Reading scheduler (change button labels and behaviors)
def my_reviewer_answerButtonList(self, _old):
    answeredCard = self.card;
    #Only manipulate buttons if Incremental Reading deck
    if(answeredCard.model()['name'] == IR_MODEL_NAME):
        l = ((1, _("Soon")),)
        cnt = mw.col.sched.answerButtons(self.card)
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
    if(answeredCard.model()['name'] == IR_MODEL_NAME): return "<div class=spacer></div>";
    else: return _old(self, i);

def my_reviewer_answerCard(self, ease, _old):
    #Get the card before scheduler kicks in, else you are looking at a different card or NONE (which gives error)
    answeredCard = self.card;

    #Always do the regular Anki scheduling logic (for non-Incremental Reading decks, and also because UI behavior is assured
    #to be consistent this way. Below code only manipulates the database, not the UI.)
    _old(self, ease);

    #Only manipulate the deck if this is an Incremental Reading deck
    if(answeredCard.model()['name'] == IR_MODEL_NAME):
        #print "Ease: " + str(ease);
        #print "Card id: " + str(answeredCard.id);
        mw.readingManager.scheduleCard(answeredCard, ease);

Reviewer._answerCard = wrap(Reviewer._answerCard, my_reviewer_answerCard, "around")
Reviewer._answerButtonList = wrap(Reviewer._answerButtonList, my_reviewer_answerButtonList, "around")
Reviewer._buttonTime = wrap(Reviewer._buttonTime, my_reviewer_buttonTime, "around")
