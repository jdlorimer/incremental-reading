# -*- coding: utf-8 -*-

from random import gauss, shuffle

from PyQt4.QtCore import Qt
from PyQt4.QtGui import (QAbstractItemView,
                         QDialog,
                         QDialogButtonBox,
                         QHBoxLayout,
                         QListWidget,
                         QListWidgetItem,
                         QPushButton,
                         QVBoxLayout)

from aqt import mw
from aqt.utils import showInfo, tooltip

SCHEDULE_SOON = 1
SCHEDULE_LATER = 2
SCHEDULE_CUSTOM = 3


class Scheduler:
    def __init__(self, settings):
        self.settings = settings

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
            text = '[ {} ]\t{}'.format(str(i).zfill(posWidth), card['title'])
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, card)
            self.cardListWidget.addItem(item)

        upButton = QPushButton('Up')
        upButton.clicked.connect(self._moveUp)
        downButton = QPushButton('Down')
        downButton.clicked.connect(self._moveDown)
        randomizeButton = QPushButton('Randomize')
        randomizeButton.clicked.connect(self._randomize)

        controlsLayout = QHBoxLayout()
        controlsLayout.addStretch()
        controlsLayout.addWidget(upButton)
        controlsLayout.addWidget(downButton)
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

    def _moveUp(self):
        selected = [self.cardListWidget.item(i)
                    for i in range(self.cardListWidget.count())
                    if self.cardListWidget.item(i).isSelected()]
        for item in selected:
            row = self.cardListWidget.row(item)
            newRow = max(0, row - 1)
            self.cardListWidget.insertItem(
                newRow, self.cardListWidget.takeItem(row))
            item.setSelected(True)

    def _moveDown(self):
        selected = [self.cardListWidget.item(i)
                    for i in range(self.cardListWidget.count())
                    if self.cardListWidget.item(i).isSelected()]
        selected.reverse()
        for item in selected:
            row = self.cardListWidget.row(item)
            newRow = min(self.cardListWidget.count(), row + 1)
            self.cardListWidget.insertItem(
                newRow, self.cardListWidget.takeItem(row))
            item.setSelected(True)

    def _randomize(self):
        allItems = [self.cardListWidget.takeItem(0)
                    for i in range(self.cardListWidget.count())]
        shuffle(allItems)
        for item in allItems:
            self.cardListWidget.addItem(item)

    def answer(self, card, ease):
        if ease == SCHEDULE_SOON:
            value = self.settings['schedSoonValue']
            randomize = self.settings['schedSoonRandom']
            method = self.settings['schedSoonMethod']
        elif ease == SCHEDULE_LATER:
            value = self.settings['schedLaterValue']
            randomize = self.settings['schedLaterRandom']
            method = self.settings['schedLaterMethod']
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

        newPos = max(1, int(newPos))
        self.reposition(card, newPos)
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
                title = note[self.settings['titleField']].encode(
                    'ascii', errors='xmlcharrefreplace').encode('string_escape')

                cardInfo.append({'id': cid,
                                 'nid': nid,
                                 'title': title})

        return cardInfo
