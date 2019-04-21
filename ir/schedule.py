# Copyright 2013 Tiago Barroso
# Copyright 2013 Frank Kmiec
# Copyright 2013-2016 Aleksej
# Copyright 2017 Christian Weiß
# Copyright 2018 Timothée Chauvin
# Copyright 2017-2019 Joseph Lorimer <joseph@lorimer.me>
#
# Permission to use, copy, modify, and distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright
# notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

from random import gauss, shuffle
from re import sub

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from anki.utils import stripHTML
from aqt import mw
from aqt.utils import showInfo, tooltip

from .util import showBrowser

SCHEDULE_EXTRACT = 0
SCHEDULE_SOON = 1
SCHEDULE_LATER = 2
SCHEDULE_CUSTOM = 3


class Scheduler:
    did = None
    cardListWidget = None

    def showDialog(self, currentCard=None):
        if currentCard:
            self.did = currentCard.did
        elif mw._selectedDeck():
            self.did = mw._selectedDeck()['id']
        else:
            return

        if not self._getCardInfo(self.did):
            showInfo('Please select an Incremental Reading deck.')
            return

        dialog = QDialog(mw)
        layout = QVBoxLayout()
        self.cardListWidget = QListWidget()
        self.cardListWidget.setAlternatingRowColors(True)
        self.cardListWidget.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        self.cardListWidget.setWordWrap(True)
        self.cardListWidget.itemDoubleClicked.connect(
            lambda: showBrowser(
                self.cardListWidget.currentItem().data(Qt.UserRole)['nid']
            )
        )

        self._updateListItems()

        upButton = QPushButton('Up')
        upButton.clicked.connect(self._moveUp)
        downButton = QPushButton('Down')
        downButton.clicked.connect(self._moveDown)
        topButton = QPushButton('Top')
        topButton.clicked.connect(self._moveToTop)
        bottomButton = QPushButton('Bottom')
        bottomButton.clicked.connect(self._moveToBottom)
        randomizeButton = QPushButton('Randomize')
        randomizeButton.clicked.connect(self._randomize)

        controlsLayout = QHBoxLayout()
        controlsLayout.addWidget(topButton)
        controlsLayout.addWidget(upButton)
        controlsLayout.addWidget(downButton)
        controlsLayout.addWidget(bottomButton)
        controlsLayout.addStretch()
        controlsLayout.addWidget(randomizeButton)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Close | QDialogButtonBox.Save
        )
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

    def _updateListItems(self):
        cardInfo = self._getCardInfo(self.did)
        self.cardListWidget.clear()
        posWidth = len(str(len(cardInfo) + 1))
        for i, card in enumerate(cardInfo, start=1):
            if self.settings['prioEnabled']:
                info = card['priority']
            else:
                info = str(i).zfill(posWidth)
            title = sub(r'\s+', ' ', stripHTML(card['title']))
            text = self.settings['organizerFormat'].format(
                info=info, title=title
            )
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, card)
            self.cardListWidget.addItem(item)

    def _moveToTop(self):
        selected = self._getSelected()
        if not selected:
            showInfo('Please select one or several items.')
            return

        selected.reverse()
        for item in selected:
            self.cardListWidget.takeItem(self.cardListWidget.row(item))
            self.cardListWidget.insertItem(0, item)
            item.setSelected(True)

        self.cardListWidget.scrollToTop()

    def _moveUp(self):
        selected = self._getSelected()
        if not selected:
            showInfo('Please select one or several items.')
            return

        if self.cardListWidget.row(selected[0]) == 0:
            return

        for item in selected:
            row = self.cardListWidget.row(item)
            self.cardListWidget.takeItem(row)
            self.cardListWidget.insertItem(row - 1, item)
            item.setSelected(True)
            self.cardListWidget.scrollToItem(item)

    def _moveDown(self):
        selected = self._getSelected()
        if not selected:
            showInfo('Please select one or several items.')
            return

        selected.reverse()

        if (
            self.cardListWidget.row(selected[0])
            == self.cardListWidget.count() - 1
        ):
            return

        for item in selected:
            row = self.cardListWidget.row(item)
            self.cardListWidget.takeItem(row)
            self.cardListWidget.insertItem(row + 1, item)
            item.setSelected(True)
            self.cardListWidget.scrollToItem(item)

    def _moveToBottom(self):
        selected = self._getSelected()
        if not selected:
            showInfo('Please select one or several items.')
            return

        for item in selected:
            self.cardListWidget.takeItem(self.cardListWidget.row(item))
            self.cardListWidget.insertItem(self.cardListWidget.count(), item)
            item.setSelected(True)

        self.cardListWidget.scrollToBottom()

    def _getSelected(self):
        return [
            self.cardListWidget.item(i)
            for i in range(self.cardListWidget.count())
            if self.cardListWidget.item(i).isSelected()
        ]

    def _randomize(self):
        allItems = [
            self.cardListWidget.takeItem(0)
            for _ in range(self.cardListWidget.count())
        ]
        if self.settings['prioEnabled']:
            maxPrio = len(self.settings['priorities']) - 1
            for item in allItems:
                priority = item.data(Qt.UserRole)['priority']
                if priority != '':
                    item.contNewPos = gauss(
                        maxPrio - int(priority), maxPrio / 20
                    )
                else:
                    item.contNewPos = float('inf')
            allItems.sort(key=lambda item: item.contNewPos)

        else:
            shuffle(allItems)

        for item in allItems:
            self.cardListWidget.addItem(item)

    def answer(self, card, ease):
        if self.settings['prioEnabled']:
            # reposition the card at the end of the organizer
            cardCount = len(self._getCardInfo(card.did))
            self.reposition(card, cardCount)
            return

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
        newOrder = cids[: newPos - 1] + [card.id] + cids[newPos - 1 :]
        mw.col.sched.sortCards(newOrder)

    def reorder(self, cids):
        mw.col.sched.forgetCards(cids)
        mw.col.sched.sortCards(cids)

    def _getCardInfo(self, did):
        cardInfo = []

        for cid, nid in mw.col.db.execute(
            'select id, nid from cards where did = ?', did
        ):
            note = mw.col.getNote(nid)
            if note.model()['name'] == self.settings['modelName']:
                if self.settings['prioEnabled']:
                    prio = note[self.settings['prioField']]
                else:
                    prio = None

                cardInfo.append(
                    {
                        'id': cid,
                        'nid': nid,
                        'title': note[self.settings['titleField']],
                        'priority': prio,
                    }
                )

        return cardInfo
