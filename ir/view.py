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
        mw.web.wheelEvent = wrap(mw.web.wheelEvent, self.saveScroll)
        mw.web.mouseReleaseEvent = wrap(mw.web.mouseReleaseEvent,
                                        self.saveScroll,
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

    def setZoom(self, factor=None):
        if factor:
            mw.web.setTextSizeMultiplier(factor)
        else:
            mw.web.setTextSizeMultiplier(
                self.settings['zoom'][str(mw.reviewer.card.id)])

    def zoomIn(self):
        if mw.reviewer.card:
            if mw.reviewer.card.model()['name'] == self.settings['modelName']:
                cid = str(mw.reviewer.card.id)

                if cid not in self.settings['zoom']:
                    self.settings['zoom'][cid] = 1

                self.settings['zoom'][cid] += self.settings['zoomStep']
                mw.web.setTextSizeMultiplier(self.settings['zoom'][cid])
            else:
                newFactor = (mw.web.textSizeMultiplier() +
                             self.settings['zoomStep'])
                mw.web.setTextSizeMultiplier(newFactor)

    def zoomOut(self):
        if mw.reviewer.card:
            if mw.reviewer.card.model()['name'] == self.settings['modelName']:
                cid = str(mw.reviewer.card.id)

                if cid not in self.settings['zoom']:
                    self.settings['zoom'][cid] = 1

                self.settings['zoom'][cid] -= self.settings['zoomStep']
                mw.web.setTextSizeMultiplier(self.settings['zoom'][cid])
            else:
                newFactor = (mw.web.textSizeMultiplier() -
                             self.settings['zoomStep'])
                mw.web.setTextSizeMultiplier(newFactor)

    def setScroll(self, position=None):
        if position is not None:
            mw.web.page().mainFrame().setScrollPosition(QPoint(0, position))
            self.saveScroll()
        else:
            position = self.settings['scroll'][str(mw.reviewer.card.id)]
            mw.web.page().mainFrame().setScrollPosition(QPoint(0, position))

    def saveScroll(self, event=None):
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
        self.setScroll(newPosition)

    def pageDown(self):
        currentPosition = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['pageScrollFactor']
        pageBottom = mw.web.page().mainFrame().scrollBarMaximum(Qt.Vertical)
        newPosition = min(pageBottom, (currentPosition + movementSize))
        self.setScroll(newPosition)

    def lineUp(self):
        currentPosition = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['lineScrollFactor']
        newPosition = max(0, (currentPosition - movementSize))
        self.setScroll(newPosition)

    def lineDown(self):
        currentPosition = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['lineScrollFactor']
        pageBottom = mw.web.page().mainFrame().scrollBarMaximum(Qt.Vertical)
        newPosition = min(pageBottom, (currentPosition + movementSize))
        self.setScroll(newPosition)

    def resetZoom(self, state, *args):
        if state in ['deckBrowser', 'overview']:
            mw.web.setTextSizeMultiplier(self.settings['generalZoom'])
        elif (state == 'review' and
              self.previousState != 'review' and
              mw.reviewer.card and
              (mw.reviewer.card.note().model()['name'] !=
               self.settings['modelName'])):
            self.setZoom(1)

        self.previousState = state
