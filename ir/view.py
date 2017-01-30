# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from PyQt4.QtCore import QPoint, Qt
from anki.hooks import wrap
from aqt import mw

from ir.util import addMenuItem, addShortcut


class ViewManager():
    def __init__(self):
        self.previousState = None
        mw.moveToState = wrap(mw.moveToState, self.resetZoom, 'before')
        mw.web.wheelEvent = wrap(mw.web.wheelEvent, self.saveScrollPosition)
        mw.web.mouseReleaseEvent = wrap(mw.web.mouseReleaseEvent,
                                        self.saveScrollPosition,
                                        'before')

    def addMenuItems(self):
        addMenuItem('Read', 'Zoom In', self.zoomIn, 'Ctrl++')
        addMenuItem('Read', 'Zoom Out', self.zoomOut, 'Ctrl+-')

    def addShortcuts(self):
        addShortcut(self.lineUp, 'Up')
        addShortcut(self.lineDown, 'Down')
        addShortcut(self.pageUp, 'PgUp')
        addShortcut(self.pageDown, 'PgDown')
        addShortcut(self.zoomIn, 'Ctrl+=')

    def zoomIn(self):
        if mw.reviewer.card:
            if mw.reviewer.card.model()['name'] == self.settings['modelName']:
                cardID = str(mw.reviewer.card.id)

                if cardID not in self.settings['zoom']:
                    self.settings['zoom'][cardID] = 1

                self.settings['zoom'][cardID] += self.settings['zoomStep']
                mw.web.setTextSizeMultiplier(self.settings['zoom'][cardID])
            else:
                newFactor = (mw.web.textSizeMultiplier() +
                             self.settings['zoomStep'])
                mw.web.setTextSizeMultiplier(newFactor)

    def zoomOut(self):
        if mw.reviewer.card:
            if mw.reviewer.card.model()['name'] == self.settings['modelName']:
                cardID = str(mw.reviewer.card.id)

                if cardID not in self.settings['zoom']:
                    self.settings['zoom'][cardID] = 1

                self.settings['zoom'][cardID] -= self.settings['zoomStep']
                mw.web.setTextSizeMultiplier(self.settings['zoom'][cardID])
            else:
                newFactor = (mw.web.textSizeMultiplier() -
                             self.settings['zoomStep'])
                mw.web.setTextSizeMultiplier(newFactor)

    def setScrollPosition(self, newPosition):
        mw.web.page().mainFrame().setScrollPosition(QPoint(0, newPosition))
        self.saveScrollPosition()

    def saveScrollPosition(self, event=None):
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

    def resetZoom(self, state, *args):
        if state in ['deckBrowser', 'overview']:
            mw.web.setTextSizeMultiplier(self.settings['generalZoom'])
        elif (state == 'review' and
              self.previousState != 'review' and
              mw.reviewer.card and
              (mw.reviewer.card.note().model()['name'] !=
               self.settings['modelName'])):
            mw.web.setTextSizeMultiplier(1)

        self.previousState = state
