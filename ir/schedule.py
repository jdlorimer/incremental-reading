import random

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDialog, QDialogButtonBox, QVBoxLayout

from aqt import mw
from aqt.utils import showInfo, tooltip
from aqt.webview import AnkiWebView

from ir.util import addMenuItem


class Scheduler():
    def addMenuItem(self):
        addMenuItem('Read', 'Organizer...', self.showDialog, 'Alt+2')

    def showDialog(self, currentCard=None):
        # Handle for dialog open without a current card from IR model
        did = None
        cid = None
        if not currentCard:
            deck = mw._selectedDeck()
            did = deck['id']
        else:
            did = currentCard.did
            cid = currentCard.id

        cardDataList = self.getCardDataList(did, cid)
        if not cardDataList:
            showInfo(_('Please select an Incremental Reading deck.'))
            return

        d = QDialog(mw)
        l = QVBoxLayout()
        w = AnkiWebView()
        l.addWidget(w)

        script = '''
        var cardList = new Array();
        '''
        index = 0
        for cardData in cardDataList:
            index += 1
            script += "card = new Object();"
            script += "card.id = " + str(cardData['id']) + ";"
            script += "card.title = '" + str(cardData['title']) + "';"
            script += "card.isCurrent = " + str(cardData['isCurrent']) + ";"
            script += "card.checkbox = document.createElement('input');"
            script += "card.checkbox.type = 'checkbox';"
            if cardData['isCurrent'] == 'true':
                script += "card.checkbox.setAttribute('checked', 'true');"
            script += "cardList[cardList.length] = card;"

        script += """
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
            for (var i = 0; i < cardList.length; i++) {
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
            if (newIndex < 0 || newIndex > (cardList.length-1)) return -1;
            if (cardList[newIndex].checkbox.checked) return -1;

            if (isTopOfRange) {
                document.getElementById('newPos').value = newIndex;
            }
            var removedCards = cardList.splice(origIndex,1);
            cardList.splice(newIndex, 0, removedCards[0]);
            return newIndex;
        }

        function moveSelectedUp() {
            var topOfRange = -1;
            for (var i = 0; i < cardList.length; i++) {
                if (cardList[i].checkbox.checked) {
                    if (topOfRange == -1) {
                        topOfRange = i;
                    }
                    if (i == topOfRange) {
                        if (document.getElementById('anchor').checked) {
                            continue; //Don't move end of range if anchored.
                        } else {
                            reposition(i, i - 1, true);
                        }
                    } else {
                        reposition(i, i - 1, false);
                    }
                }
            }
            buildCardData();
        }

        function moveSelectedDown() {
            var topOfRange = -1;
            var bottomOfRange = -1;
            for (var i = 0; i < cardList.length; i++) {
                if (cardList[i].checkbox.checked) {
                    if (topOfRange == -1) {
                        topOfRange = i;
                    }
                    bottomOfRange = i;
                }
            }
            for (var i = cardList.length-1; i > -1; i--) {
                if (cardList[i].checkbox.checked) {
                    if (i == bottomOfRange &&
                            document.getElementById('anchor').checked) {
                        continue; //Don't move end of range if anchored.
                    }
                    if (i == topOfRange) {
                        reposition(i, i + 1, true);
                    } else {
                        reposition(i, i + 1, false);
                    }
                }
            }
            buildCardData();
        }

        function selectAll() {
            for (var i = 0; i < cardList.length; i++) {
                cardList[i].checkbox.checked = true;
            }
        }

        function selectNone() {
            for (var i = 0; i < cardList.length; i++) {
                cardList[i].checkbox.checked = false;
            }
        }

        function directMove() {
            var newIndex = document.getElementById('newPos').value;
            var topOfRange = -1;
            origIndex = -1;
            for (var i = 0; i < cardList.length; i++) {
                if (cardList[i].checkbox.checked) {
                    if (topOfRange == -1) {
                        topOfRange = i;
                    }
                    if (origIndex == -1) {
                        origIndex = i;
                        sizeOfMove = (newIndex - origIndex);
                    }
                }
            }
            if (sizeOfMove < 0) {
                for (var i = 0; i < cardList.length; i++) {
                    if (cardList[i].checkbox.checked) {
                        if (i == topOfRange) {
                            reposition(i, i + sizeOfMove, true);
                        } else {
                            reposition(i, i + sizeOfMove, false);
                        }
                    }
                }
            } else {
                for (var i = cardList.length-1; i > -1; i--) {
                    if (cardList[i].checkbox.checked) {
                        if (i == topOfRange) {
                            reposition(i, i + sizeOfMove, true);
                        } else {
                            reposition(i, i + sizeOfMove, false);
                        }
                    }
                }
            }
            buildCardData();
        }

        function updatePositions() {
            var cids = new Array();
            for (var i=0; i < cardList.length; i++) {
                cids[cids.length] = parseInt(cardList[i].id);
            }
            return cids.join();
        };
        """

        newPosField = "<span style='font-weight:bold'>Card Position: </span><input type='text' id='newPos' size='5' value='0' />&nbsp;<span style='font-weight:bold'>of " + str(len(cardDataList)) + "</span>&nbsp;&nbsp;"
        newPosField += "<input type='button' value='Apply' onclick='directMove()' />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='font-weight:bold'>Pin Top/Bottom? </span><input type='checkbox' id='anchor'/>"

        upDownButtons = "<input type='button' value='Move Up' onclick='moveSelectedUp()'/><input type='button' value='Move Down' onclick='moveSelectedDown()'/>"
        upDownButtons += "<input type='button' value='Select All' onclick='selectAll()'/><input type='button' value='Select None' onclick='selectNone()'/>"

        html = "<html><head><script>" + script + "</script></head><body onLoad='buildCardData()'>"
        html += "<p>" + newPosField
        html += "<p>" + upDownButtons
        html += "<div id='cardList'></div>"
        html += "</body></html>"
        w.stdHtml(html)
        bb = QDialogButtonBox(QDialogButtonBox.Close | QDialogButtonBox.Save)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        bb.setOrientation(Qt.Horizontal)
        l.addWidget(bb)
        d.setLayout(l)
        d.setWindowModality(Qt.WindowModal)
        d.resize(500, 500)
        choice = d.exec_()
        if choice == 1:
            cids = w.page().mainFrame().evaluateJavaScript('updatePositions()')
            self.repositionCards(cids)
        elif currentCard:
            self.repositionCard(currentCard, -1)

    def scheduleCard(self, card, ease):
        cnt = -1
        pct = -1

        if ease == 1:
            if self.settings['schedSoonType'] == 'pct':
                if self.settings['schedSoonRandom']:
                    pct = float(random.randint(1, self.settings['schedSoonInt'])) / float(100)
                else:
                    pct = float(self.settings['schedSoonInt']) / float(100)
            else:
                cnt = self.settings['schedSoonInt']
                if self.settings['schedSoonRandom']:
                    cnt = random.randint(1, self.settings['schedSoonInt'])
        elif ease == 2:
            if self.settings['schedSoonType'] == 'pct':
                if self.settings['schedLaterRandom']:
                    pct = float(random.randint(self.settings['schedSoonInt'], self.settings['schedLaterInt'])) / float(100)
                else:
                    pct = float(self.settings['schedLaterInt']) / float(100)
            else:
                cnt = self.settings['schedLaterInt']
                if self.settings['schedLaterRandom']:
                    cnt = random.randint(self.settings['schedSoonInt'],
                                         self.settings['schedLaterInt'])
        elif ease == 3:
            self.showDialog(card)
            return
        elif ease == 4:
            pct = 1
        if pct > -1:
            cds = self.getIRCards(card)
            pos = int(len(cds) * pct)
            tooltip(_("Card moved (" + str(int(100*pct)) + "%) to position:  " + str(pos)), period=1500)
        elif cnt > -1:
            pos = cnt
            tooltip(_("Card moved to position:  " + str(pos)), period=1500)
        else:
            pos = 5
            tooltip(_("Card moved by default to position:  " + str(pos)), period=1500)
        self.repositionCard(card, pos)

    def repositionCard(self, card, pos):
        cids = []
        cids.append(card.id)
        mw.col.sched.forgetCards(cids)

        # If opened dialog and chose not to specify a position, card ends up at
        #   end of NEW queue by default
        if pos < 0:
            return

        cids = self.getIRCards(card)
        index = 0
        newCardOrder = []
        for cid in cids:
            if cid != card.id:
                if index == pos:
                    newCardOrder.append(card.id)
                    index += 1
                    newCardOrder.append(cid)
                else:
                    newCardOrder.append(cid)
            elif index == pos:
                    newCardOrder.append(card.id)
            index += 1
        mw.col.sched.sortCards(newCardOrder)

    def repositionCards(self, cids):
        cids = [int(id) for id in cids.split(',')]
        mw.col.sched.forgetCards(cids)
        mw.col.sched.sortCards(cids)

    def getIRCards(self, card):
        cids = []
        for id, nid in mw.col.db.execute(
                'select id, nid from cards where did = ' + str(card.did)):
            note = mw.col.getNote(nid)
            if note.model()['name'] == self.settings['modelName']:
                cids.append(id)
        return cids

    def getCardDataList(self, did, cid):
        cardDataList = []
        note = None
        for id, nid in mw.col.db.execute(
                'select id, nid from cards where did = ' + str(did)):
            cardData = {}
            cardData['id'] = id
            cardData['nid'] = nid
            note = mw.col.getNote(nid)

            if note.model()['name'] != self.settings['modelName']:
                continue

            cardData['title'] = note['Title'][:64]

            cardData['title'] = cardData['title'].encode(
                'ascii', errors='xmlcharrefreplace').encode('string_escape')

            if cid == id:
                cardData['isCurrent'] = 'true'
            else:
                cardData['isCurrent'] = 'false'

            cardDataList.append(cardData)
        return cardDataList
