# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from PyQt4.QtCore import QPoint, Qt

from anki.hooks import wrap
from aqt import mw

from ir.util import addMenuItem, addShortcut, viewingIrText


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
            mw.web.setZoomFactor(factor)
        else:
            mw.web.setZoomFactor(
                self.settings['zoom'][str(mw.reviewer.card.id)])

    def zoomIn(self):
        if viewingIrText():
            cid = str(mw.reviewer.card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            self.settings['zoom'][cid] += self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['zoom'][cid])
        elif mw.reviewer.card:
            newFactor = mw.web.zoomFactor() + self.settings['zoomStep']
            mw.web.setZoomFactor(newFactor)

    def zoomOut(self):
        if viewingIrText():
            cid = str(mw.reviewer.card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            self.settings['zoom'][cid] -= self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['zoom'][cid])
        elif mw.reviewer.card:
            newFactor = mw.web.zoomFactor() - self.settings['zoomStep']
            mw.web.setZoomFactor(newFactor)

    def setScroll(self, pos=None):
        if pos is None:
            savedPos = self.settings['scroll'][str(mw.reviewer.card.id)]
            mw.web.page().mainFrame().setScrollPosition(QPoint(0, savedPos))
        else:
            mw.web.page().mainFrame().setScrollPosition(QPoint(0, pos))
            self.saveScroll()

    def saveScroll(self, event=None):
        if viewingIrText():
            pos = mw.web.page().mainFrame().scrollPosition().y()
            self.settings['scroll'][str(mw.reviewer.card.id)] = pos

    def pageUp(self):
        currentPos = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['pageScrollFactor']
        newPos = max(0, (currentPos - movementSize))
        self.setScroll(newPos)

    def pageDown(self):
        currentPos = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['pageScrollFactor']
        pageBottom = mw.web.page().mainFrame().scrollBarMaximum(Qt.Vertical)
        newPos = min(pageBottom, (currentPos + movementSize))
        self.setScroll(newPos)

    def lineUp(self):
        currentPos = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['lineScrollFactor']
        newPos = max(0, (currentPos - movementSize))
        self.setScroll(newPos)

    def lineDown(self):
        currentPos = mw.web.page().mainFrame().scrollPosition().y()
        pageHeight = mw.web.page().viewportSize().height()
        movementSize = pageHeight * self.settings['lineScrollFactor']
        pageBottom = mw.web.page().mainFrame().scrollBarMaximum(Qt.Vertical)
        newPos = min(pageBottom, (currentPos + movementSize))
        self.setScroll(newPos)

    def resetZoom(self, state, *args):
        if state in ['deckBrowser', 'overview']:
            mw.web.setZoomFactor(self.settings['generalZoom'])
        elif (state == 'review' and
              self.previousState != 'review' and
              mw.reviewer.card and
              (mw.reviewer.card.note().model()['name'] !=
               self.settings['modelName'])):
            self.setZoom(1)

        self.previousState = state
