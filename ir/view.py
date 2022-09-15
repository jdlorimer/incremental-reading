# Copyright 2013 Tiago Barroso
# Copyright 2013 Frank Kmiec
# Copyright 2013-2016 Aleksej
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
from anki.cards import Card
from anki.hooks import addHook
from aqt import mw
from aqt import gui_hooks

from .util import isIrCard, loadFile, viewingIrText


class ViewManager:
    def __init__(self):
        self.scrollScript = loadFile('web', 'scroll.js')
        self.textScript = loadFile('web', 'text.js')
        self.widthScript = loadFile('web', 'width.js')
        self.zoomFactor = 1
        addHook('afterStateChange', self.resetZoom)
        gui_hooks.card_will_show.append(self._prepare_card)
        mw.web.page().scrollPositionChanged.connect(self.saveScroll)

    def _prepare_card(self, html: str, card: Card, kind: str) -> str:
        if (isIrCard(card) and self.settings['limitWidth']) or self.settings['limitWidthAll']:
            js = self.widthScript.format(maxWidth=self.settings['maxWidth'])
        else:
            js = ''

        if isIrCard(card) and kind.startswith('review'):
            cid = str(card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            if cid not in self.settings['scroll']:
                self.settings['scroll'][cid] = 0

            self.setZoom()
            js += self.textScript
            js += self.scrollScript.format(
                savedPos=self.settings['scroll'][cid],
                lineScrollFactor=self.settings['lineScrollFactor'],
                pageScrollFactor=self.settings['pageScrollFactor'],
            )

        if js:
            html += '<script>' + js + '</script>'

        return html

    def setZoom(self, factor=None):
        if factor:
            mw.web.setZoomFactor(factor)
        else:
            mw.web.setZoomFactor(
                self.settings['zoom'][str(mw.reviewer.card.id)]
            )

    def zoomIn(self):
        if viewingIrText():
            cid = str(mw.reviewer.card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            self.settings['zoom'][cid] += self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['zoom'][cid])
        elif mw.state == 'review':
            self.zoomFactor += self.settings['zoomStep']
            mw.web.setZoomFactor(self.zoomFactor)
        else:
            self.settings['generalZoom'] += self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['generalZoom'])

    def zoomOut(self):
        if viewingIrText():
            cid = str(mw.reviewer.card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            self.settings['zoom'][cid] -= self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['zoom'][cid])
        elif mw.state == 'review':
            self.zoomFactor -= self.settings['zoomStep']
            mw.web.setZoomFactor(self.zoomFactor)
        else:
            self.settings['generalZoom'] -= self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['generalZoom'])

    def saveScroll(self, event=None):
        if viewingIrText():

            def callback(currentPos):
                self.settings['scroll'][str(mw.reviewer.card.id)] = currentPos

            mw.web.evalWithCallback('window.pageYOffset;', callback)

    def resetZoom(self, state, *args):
        if not hasattr(self, 'settings'):
            return

        if state in ['deckBrowser', 'overview']:
            mw.web.setZoomFactor(self.settings['generalZoom'])
        elif state == 'review' and not isIrCard(mw.reviewer.card):
            self.setZoom(self.zoomFactor)
