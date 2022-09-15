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
from aqt.main import MainWindowState

from .util import isIrCard, loadFile, viewingIrText


class ViewManager:
    def __init__(self):
        self._scroll_script = loadFile('web', 'scroll.js')
        self._text_script = loadFile('web', 'text.js')
        self._width_script = loadFile('web', 'width.js')
        self._zoom_factor = 1

        addHook('afterStateChange', self.reset_zoom)
        gui_hooks.card_will_show.append(self._prepare_card)
        mw.web.page().scrollPositionChanged.connect(self._save_scroll)

    def reset_zoom(self, state: MainWindowState, *args):
        if not hasattr(self, 'settings'):
            return

        if state in ['deckBrowser', 'overview']:
            mw.web.setZoomFactor(self.settings['generalZoom'])
        elif state == 'review' and not isIrCard(mw.reviewer.card):
            self._set_zoom(self._zoom_factor)

    def zoom_in(self):
        if viewingIrText():
            cid = str(mw.reviewer.card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            self.settings['zoom'][cid] += self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['zoom'][cid])
        elif mw.state == 'review':
            self._zoom_factor += self.settings['zoomStep']
            mw.web.setZoomFactor(self._zoom_factor)
        else:
            self.settings['generalZoom'] += self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['generalZoom'])

    def zoom_out(self):
        if viewingIrText():
            cid = str(mw.reviewer.card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            self.settings['zoom'][cid] -= self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['zoom'][cid])
        elif mw.state == 'review':
            self._zoom_factor -= self.settings['zoomStep']
            mw.web.setZoomFactor(self._zoom_factor)
        else:
            self.settings['generalZoom'] -= self.settings['zoomStep']
            mw.web.setZoomFactor(self.settings['generalZoom'])

    def _prepare_card(self, html: str, card: Card, kind: str) -> str:
        if (isIrCard(card) and self.settings['limitWidth']) or self.settings['limitWidthAll']:
            js = self._width_script.format(maxWidth=self.settings['maxWidth'])
        else:
            js = ''

        if isIrCard(card) and kind.startswith('review'):
            cid = str(card.id)

            if cid not in self.settings['zoom']:
                self.settings['zoom'][cid] = 1

            if cid not in self.settings['scroll']:
                self.settings['scroll'][cid] = 0

            self._set_zoom()
            js += self._text_script
            js += self._scroll_script.format(
                savedPos=self.settings['scroll'][cid],
                lineScrollFactor=self.settings['lineScrollFactor'],
                pageScrollFactor=self.settings['pageScrollFactor'],
            )

        if js:
            html += '<script>' + js + '</script>'

        return html

    def _save_scroll(self, event=None):
        if viewingIrText():

            def callback(current_pos):
                self.settings['scroll'][str(mw.reviewer.card.id)] = current_pos

            mw.web.evalWithCallback('window.pageYOffset;', callback)

    def _set_zoom(self, factor=None):
        if factor:
            mw.web.setZoomFactor(factor)
        else:
            mw.web.setZoomFactor(
                self.settings['zoom'][str(mw.reviewer.card.id)]
            )