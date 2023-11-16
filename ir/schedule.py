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

try:
    from PyQt6.QtCore import Qt
except ModuleNotFoundError:
    from PyQt5.QtCore import Qt

from anki.cards import Card
from anki.utils import strip_html
from aqt import mw
from aqt.qt import (QAbstractItemView, QDialog, QDialogButtonBox, QHBoxLayout,
                    QListWidget, QListWidgetItem, QPushButton, QVBoxLayout)
from aqt.utils import showInfo, tooltip

from .settings import SettingsManager
from .util import showBrowser

SCHEDULE_EXTRACT = 0
SCHEDULE_SOON = 1
SCHEDULE_LATER = 2
SCHEDULE_CUSTOM = 3


class Scheduler:
    _deckId = None
    _cardListWidget = None
    _settings: SettingsManager = None

    def changeProfile(self, settings: SettingsManager):
        self._settings = settings

    def showDialog(self, currentCard: Card = None):
        if currentCard:
            self._deckId = currentCard.did
        elif mw._selectedDeck():
            self._deckId = mw._selectedDeck()['id']
        else:
            return

        if not self._getCardInfo(self._deckId):
            showInfo('Please select an Incremental Reading deck.')
            return

        dialog = QDialog(mw)
        layout = QVBoxLayout()
        self._cardListWidget = QListWidget()
        self._cardListWidget.setAlternatingRowColors(True)
        self._cardListWidget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self._cardListWidget.setWordWrap(True)
        self._cardListWidget.itemDoubleClicked.connect(
            lambda: showBrowser(
                self._cardListWidget.currentItem().data(Qt.ItemDataRole.UserRole)['nid']
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
            QDialogButtonBox.StandardButton.Close | QDialogButtonBox.StandardButton.Save
        )
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        buttonBox.setOrientation(Qt.Orientation.Horizontal)

        layout.addLayout(controlsLayout)
        layout.addWidget(self._cardListWidget)
        layout.addWidget(buttonBox)

        dialog.setLayout(layout)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.resize(500, 500)
        choice = dialog.exec()

        if choice == 1:
            cids = []
            for i in range(self._cardListWidget.count()):
                card = self._cardListWidget.item(i).data(Qt.ItemDataRole.UserRole)
                cids.append(card['id'])

            self.reorder(cids)

    def _updateListItems(self):
        cardInfo = self._getCardInfo(self._deckId)
        self._cardListWidget.clear()
        posWidth = len(str(len(cardInfo) + 1))
        for i, card in enumerate(cardInfo, start=1):
            if self._settings['prioEnabled']:
                info = card['priority']
            else:
                info = str(i).zfill(posWidth)
            title = sub(r'\s+', ' ', strip_html(card['title']))
            text = self._settings['organizerFormat'].format(
                info=info, title=title
            )
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, card)
            self._cardListWidget.addItem(item)

    def _moveToTop(self):
        selected = self._getSelected()
        if not selected:
            showInfo('Please select one or several items.')
            return

        selected.reverse()
        for item in selected:
            self._cardListWidget.takeItem(self._cardListWidget.row(item))
            self._cardListWidget.insertItem(0, item)
            item.setSelected(True)

        self._cardListWidget.scrollToTop()

    def _moveUp(self):
        selected = self._getSelected()
        if not selected:
            showInfo('Please select one or several items.')
            return

        if self._cardListWidget.row(selected[0]) == 0:
            return

        for item in selected:
            row = self._cardListWidget.row(item)
            self._cardListWidget.takeItem(row)
            self._cardListWidget.insertItem(row - 1, item)
            item.setSelected(True)
            self._cardListWidget.scrollToItem(item)

    def _moveDown(self):
        selected = self._getSelected()
        if not selected:
            showInfo('Please select one or several items.')
            return

        selected.reverse()

        if (
            self._cardListWidget.row(selected[0])
            == self._cardListWidget.count() - 1
        ):
            return

        for item in selected:
            row = self._cardListWidget.row(item)
            self._cardListWidget.takeItem(row)
            self._cardListWidget.insertItem(row + 1, item)
            item.setSelected(True)
            self._cardListWidget.scrollToItem(item)

    def _moveToBottom(self):
        selected = self._getSelected()
        if not selected:
            showInfo('Please select one or several items.')
            return

        for item in selected:
            self._cardListWidget.takeItem(self._cardListWidget.row(item))
            self._cardListWidget.insertItem(self._cardListWidget.count(), item)
            item.setSelected(True)

        self._cardListWidget.scrollToBottom()

    def _getSelected(self):
        return [
            self._cardListWidget.item(i)
            for i in range(self._cardListWidget.count())
            if self._cardListWidget.item(i).isSelected()
        ]

    def _randomize(self):
        allItems = [
            self._cardListWidget.takeItem(0)
            for _ in range(self._cardListWidget.count())
        ]
        if self._settings['prioEnabled']:
            maxPrio = len(self._settings['priorities']) - 1
            for item in allItems:
                priority = item.data(Qt.ItemDataRole.UserRole)['priority']
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
            self._cardListWidget.addItem(item)

    def answer(self, card: Card, ease: int):
        if self._settings['prioEnabled']:
            # reposition the card at the end of the organizer
            cardCount = len(self._getCardInfo(card.did))
            self.reposition(card, cardCount)
            return

        if ease == SCHEDULE_EXTRACT:
            value = self._settings['extractValue']
            randomize = self._settings['extractRandom']
            method = self._settings['extractMethod']
        elif ease == SCHEDULE_SOON:
            value = self._settings['soonValue']
            randomize = self._settings['soonRandom']
            method = self._settings['soonMethod']
        elif ease == SCHEDULE_LATER:
            value = self._settings['laterValue']
            randomize = self._settings['laterRandom']
            method = self._settings['laterMethod']
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
        mw.col.sched.reposition_new_cards(newOrder, starting_from=1, step_size=1, randomize=False, shift_existing=False)

    def reorder(self, cids):
        mw.col.sched.forgetCards(cids)
        mw.col.sched.reposition_new_cards(cids, starting_from=1, step_size=1, randomize=False, shift_existing=False)

    def _getCardInfo(self, did):
        cardInfo = []

        for cid, nid in mw.col.db.execute(
            'select id, nid from cards where did = ?', did
        ):
            note = mw.col.get_note(nid)
            if note.note_type()['name'] == self._settings['modelName']:
                if self._settings['prioEnabled']:
                    prio = note[self._settings['prioField']]
                else:
                    prio = None

                cardInfo.append(
                    {
                        'id': cid,
                        'nid': nid,
                        'title': note[self._settings['titleField']],
                        'priority': prio,
                    }
                )

        return cardInfo
