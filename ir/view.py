from anki.hooks import addHook
from aqt import mw

from ir.util import addMenuItem, addShortcut, viewingIrText


class ViewManager():
    def __init__(self):
        self.previousState = None
        addHook('afterStateChange', self.resetZoom)
        mw.web.page().scrollPositionChanged.connect(self.saveScroll)

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

    def saveScroll(self, event=None):
        if viewingIrText():
            def callback(currentPos):
                self.settings['scroll'][str(mw.reviewer.card.id)] = currentPos

            mw.web.evalWithCallback('window.pageYOffset;', callback)

    def pageUp(self):
        currentPos = self.settings['scroll'][str(mw.reviewer.card.id)]
        movementSize = self.viewportHeight * self.settings['pageScrollFactor']
        newPos = max(0, (currentPos - movementSize))
        mw.web.eval('window.scrollTo(0, {});'.format(newPos))

    def pageDown(self):
        currentPos = self.settings['scroll'][str(mw.reviewer.card.id)]
        movementSize = self.viewportHeight * self.settings['pageScrollFactor']
        newPos = min(self.pageBottom, (currentPos + movementSize))
        mw.web.eval('window.scrollTo(0, {});'.format(newPos))

    def lineUp(self):
        currentPos = self.settings['scroll'][str(mw.reviewer.card.id)]
        movementSize = self.viewportHeight * self.settings['lineScrollFactor']
        newPos = max(0, (currentPos - movementSize))
        mw.web.eval('window.scrollTo(0, {});'.format(newPos))

    def lineDown(self):
        currentPos = self.settings['scroll'][str(mw.reviewer.card.id)]
        movementSize = self.viewportHeight * self.settings['lineScrollFactor']
        newPos = min(self.pageBottom, (currentPos + movementSize))
        mw.web.eval('window.scrollTo(0, {});'.format(newPos))

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
