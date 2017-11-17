from random import gauss, shuffle

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractItemView,
                             QDialog,
                             QDialogButtonBox,
                             QHBoxLayout,
                             QListWidget,
                             QListWidgetItem,
                             QPushButton,
                             QVBoxLayout)

from anki.utils import stripHTML
from aqt import mw
from aqt.utils import showInfo, tooltip

SCHEDULE_EXTRACT = 0
SCHEDULE_SOON = 1
SCHEDULE_LATER = 2
SCHEDULE_CUSTOM = 3


class Scheduler:
    def showDialog(self, currentCard=None):
        if currentCard:
            did = currentCard.did
        else:
            did = mw._selectedDeck()['id']

        cardInfo = self._getCardInfo(did)
        if not cardInfo:
            showInfo('Please select an Incremental Reading deck.')
            return

        dialog = QDialog(mw)
        layout = QVBoxLayout()
        self.cardListWidget = QListWidget()
        self.cardListWidget.setSelectionMode(
            QAbstractItemView.ExtendedSelection)

        posWidth = len(str(len(cardInfo) + 1))
        for i, card in enumerate(cardInfo, start=1):
            text = '❰ {} ❱\t{}'.format(
                str(i).zfill(posWidth), stripHTML(card['title']))
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, card)
            self.cardListWidget.addItem(item)

        upButton = QPushButton('Up')
        upButton.clicked.connect(self._moveUp)
        downButton = QPushButton('Down')
        downButton.clicked.connect(self._moveDown)
        randomizeButton = QPushButton('Randomize')
        randomizeButton.clicked.connect(self._randomize)
        firstButton = QPushButton('First Position')
        firstButton.clicked.connect(self._firstPos)
        lastButton = QPushButton('Last Position')
        lastButton.clicked.connect(self._lastPos)

        controlsLayout = QHBoxLayout()
        controlsLayout.addStretch()
        controlsLayout.addWidget(firstButton)
        controlsLayout.addWidget(upButton)
        controlsLayout.addWidget(downButton)
        controlsLayout.addWidget(lastButton)
        controlsLayout.addWidget(randomizeButton)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Close |
                                     QDialogButtonBox.Save)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        buttonBox.setOrientation(Qt.Horizontal)

        layout.addLayout(controlsLayout)
        layout.addWidget(self.cardListWidget)
        layout.addWidget(buttonBox)

        dialog.setLayout(layout)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.resize(500, 500)
        choice = dialog.exec_()

        if choice == 1:
            cids = []
            for i in range(self.cardListWidget.count()):
                card = self.cardListWidget.item(i).data(Qt.UserRole)
                cids.append(card['id'])

            self.reorder(cids)

    def _firstPos(self):
        selected = [self.cardListWidget.item(i)
                    for i in range(self.cardListWidget.count())
                    if self.cardListWidget.item(i).isSelected()]
        selected.reverse()
        for item in selected:
            row = self.cardListWidget.row(item)
            newRow = 0
            self.cardListWidget.takeItem(row)
            self.cardListWidget.insertItem(newRow, item)
            item.setSelected(True)
    def _moveUp(self):
        selected = [self.cardListWidget.item(i)
                    for i in range(self.cardListWidget.count())
                    if self.cardListWidget.item(i).isSelected()]
        for item in selected:
            row = self.cardListWidget.row(item)
            newRow = max(0, row - 1)
            self.cardListWidget.takeItem(row)
            self.cardListWidget.insertItem(newRow, item)
            item.setSelected(True)

    def _moveDown(self):
        selected = [self.cardListWidget.item(i)
                    for i in range(self.cardListWidget.count())
                    if self.cardListWidget.item(i).isSelected()]
        selected.reverse()
        for item in selected:
            row = self.cardListWidget.row(item)
            newRow = min(self.cardListWidget.count(), row + 1)
            self.cardListWidget.takeItem(row)
            self.cardListWidget.insertItem(newRow, item)
            item.setSelected(True)
    def _lastPos(self):
        selected = [self.cardListWidget.item(i)
                    for i in range(self.cardListWidget.count())
                    if self.cardListWidget.item(i).isSelected()]
        for item in selected:
            row = self.cardListWidget.row(item)
            newRow = self.cardListWidget.count()
            self.cardListWidget.takeItem(row)
            self.cardListWidget.insertItem(newRow, item)
            item.setSelected(True)  

    def _randomize(self):
        allItems = [self.cardListWidget.takeItem(0)
                    for i in range(self.cardListWidget.count())]
        shuffle(allItems)
        for item in allItems:
            self.cardListWidget.addItem(item)

    def answer(self, card, ease):
        if ease == SCHEDULE_EXTRACT:
            value = self.settings['extractValue']
            randomize = self.settings['extractRandom']
            method = self.settings['extractMethod']
        elif ease == SCHEDULE_SOON:
            value = self.settings['soonValue']
            randomize = self.settings['soonRandom']
            method = self.settings['soonMethod']
        elif ease == SCHEDULE_LATER:
            value = self.settings['laterValue']
            randomize = self.settings['laterRandom']
            method = self.settings['laterMethod']
        elif ease == SCHEDULE_CUSTOM:
            self.reposition(card, 1)
            self.showDialog(card)
            return

        if method == 'percent':
            totalCards = len([c['id'] for c in self._getCardInfo(card.did)])
            newPos = totalCards * (value / 100)
        elif method == 'count':
            newPos = value

        if randomize:
            newPos = gauss(newPos, newPos / 10)

        newPos = max(1, round(newPos))
        self.reposition(card, newPos)

        if ease != SCHEDULE_EXTRACT:
            tooltip('Card moved to position {}'.format(newPos))

    def reposition(self, card, newPos):
        cids = [c['id'] for c in self._getCardInfo(card.did)]
        mw.col.sched.forgetCards(cids)
        cids.remove(card.id)
        newOrder = cids[:newPos-1] + [card.id] + cids[newPos-1:]
        mw.col.sched.sortCards(newOrder)

    def reorder(self, cids):
        mw.col.sched.forgetCards(cids)
        mw.col.sched.sortCards(cids)

    def _getCardInfo(self, did):
        cardInfo = []

        for cid, nid in mw.col.db.execute(
                'select id, nid from cards where did = ?',
                did):
            note = mw.col.getNote(nid)
            if note.model()['name'] == self.settings['modelName']:
                cardInfo.append({'id': cid,
                                 'nid': nid,
                                 'title': note[self.settings['titleField']]})

        return cardInfo
