from anki.hooks import addHook
from aqt import mw

from .util import isIrCard, loadJsFile, viewingIrText


class ViewManager:
    def __init__(self, settings):
        self.settings = settings
        self.scrollScript = loadJsFile('scroll')
        self.textScript = loadJsFile('text')
        self.widthScript = loadJsFile('width')
        self.zoomFactor = 1
        self.resetZoom('deckBrowser')
        addHook('afterStateChange', self.resetZoom)
        addHook('prepareQA', self.prepareCard)
        mw.web.page().scrollPositionChanged.connect(self.saveScroll)

    def prepareCard(self, html, card, context):
        if (isIrCard(card) and self.settings['limitWidth'] or
                self.settings['limitGlobalWidth']):
            js = self.widthScript.format(maxWidth=self.settings['maxWidth'])
        else:
            js = ''

        if isIrCard(card):
            mw.web.onBridgeCmd = self.storePageInfo
            cid = str(card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            if cid not in self.settings['scroll']:
                self.settings['scroll'][cid] = 0

            self.setZoom()
            js += self.textScript
            js += self.scrollScript.format(
                savedPos=self.settings['scroll'][cid])

        if js:
            return html + '<script>' + js + '</script>'
        else:
            return html

    def storePageInfo(self, cmd):
        if cmd == 'store':
            def callback(pageInfo):
                self.viewportHeight, self.pageBottom = pageInfo

            mw.web.evalWithCallback(
                '[window.innerHeight, document.body.scrollHeight];',
                callback)

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
            self.zoomFactor += self.settings['zoomStep']
            mw.web.setZoomFactor(self.zoomFactor)

    def zoomOut(self):
        if viewingIrText():
            cid = str(mw.reviewer.card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            self.settings['zoom'][cid] -= self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['zoom'][cid])
        elif mw.reviewer.card:
            self.zoomFactor -= self.settings['zoomStep']
            mw.web.setZoomFactor(self.zoomFactor)

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
        elif state == 'review' and not isIrCard(mw.reviewer.card):
            self.setZoom(self.zoomFactor)
