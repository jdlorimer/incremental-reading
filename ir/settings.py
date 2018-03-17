# Copyright 2017 Christian Weiß
# Copyright 2018 Timothée Chauvin
# Copyright 2017-2018 Luo Li-Yan <joseph.lorimer13@gmail.com>
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

from functools import partial
import json
import os

from anki.hooks import addHook
from aqt import mw
from aqt.utils import showInfo

from ._version import __version__
from .about import IR_GITHUB_URL
from .util import addMenuItem, setMenuVisibility, updateModificationTime


class SettingsManager:
    def __init__(self):
        addHook('unloadProfile', self.save)

        self.defaults = {
            'badTags': ['iframe', 'script'],
            'boldSeq': 'Ctrl+B',
            'copyTitle': False,
            'doNotUpdate': ['doNotUpdate',
                            'feedLog',
                            'modified',
                            'quickKeys',
                            'scroll',
                            'zoom'],
            'editExtract': False,
            'editSource': False,
            'extractBgColor': 'Green',
            'extractDeck': None,
            'extractKey': 'x',
            'extractMethod': 'percent',
            'extractRandom': True,
            'extractTextColor': 'White',
            'extractValue': 30,
            'feedLog': {},
            'generalZoom': 1,
            'highlightBgColor': 'Yellow',
            'highlightKey': 'h',
            'highlightTextColor': 'Black',
            'importDeck': None,
            'isQuickKey': False,
            'italicSeq': 'Ctrl+I',
            'laterMethod': 'percent',
            'laterRandom': True,
            'laterValue': 50,
            'limitWidth': True,
            'limitWidthAll': False,
            'lineScrollFactor': 0.05,
            'maxWidth': 600,
            'modelName': 'IR3',
            'modelNameBis': 'IR3+priority',
            'modified': [],
            'overlaySeq': 'Ctrl+Shift+O',
            'pageScrollFactor': 0.5,
            'plainText': False,
            'prioEnabled': False,
            'priorities': ('', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'),
            'priorityField': 'Priority',
            'quickKeys': {},
            'removeKey': 'z',
            'scheduleExtract': True,
            'scroll': {},
            'soonMethod': 'percent',
            'soonRandom': True,
            'soonValue': 10,
            'sourceField': 'Source',
            'sourceFormat': '{url} ({date})',
            'strikeSeq': 'Ctrl+S',
            'textField': 'Text',
            'titleField': 'Title',
            'underlineSeq': 'Ctrl+U',
            'undoKey': 'u',
            'userAgent': 'IR/{} (+{})'.format(__version__, IR_GITHUB_URL),
            'version': __version__,
            'zoom': {},
            'zoomStep': 0.1,
        }

        self.load()

    def __setitem__(self, key, value):
        if (self.settings[key] != value and
                key not in self.settings['modified']):
            self.settings['modified'].append(key)

        self.settings[key] = value

    def __getitem__(self, key):
        return self.settings[key]

    def load(self):
        self.updated = False
        self.mediaDir = os.path.join(mw.pm.profileFolder(), 'collection.media')
        self.jsonPath = os.path.join(self.mediaDir, '_ir.json')

        if os.path.isfile(self.jsonPath):
            with open(self.jsonPath, encoding='utf-8') as jsonFile:
                self.settings = json.load(jsonFile)

            if ('version' not in self.settings or
                    self.settings['version'] != __version__):
                self._update()
        else:
            self.settings = self.defaults

        if self.updated:
            showInfo('Your Incremental Reading settings have been updated.')

    def _update(self):
        self.settings['version'] = self.defaults['version']
        self._addMissing()
        self._removeOutdated()
        self._updateUnmodified()

    def _addMissing(self):
        for k, v in self.defaults.items():
            if k not in self.settings:
                self.settings[k] = v
                self.updated = True

    def _removeOutdated(self):
        required = [
            'alt',
            'ctrl',
            'editExtract',
            'editSource',
            'extractBgColor',
            'extractDeck',
            'extractTextColor',
            'isQuickKey',
            'modelName',
            'regularKey',
            'shift',
            'sourceField',
            'tags',
            'textField',
        ]

        for keyCombo, settings in self.settings['quickKeys'].copy().items():
            for k in required:
                if k not in settings:
                    self.settings['quickKeys'].pop(keyCombo)
                    self.updated = True
                    break

    def _updateUnmodified(self):
        for k in self.settings:
            if k in self.settings['doNotUpdate']:
                continue

            if k in self.settings['modified']:
                continue

            if self.settings[k] == self.defaults[k]:
                continue

            self.settings[k] = self.defaults[k]
            self.updated = True

    def save(self):
        with open(self.jsonPath, 'w', encoding='utf-8') as jsonFile:
            json.dump(self.settings, jsonFile)

        updateModificationTime(self.mediaDir)

    def loadMenuItems(self):
        menuName = 'Read::Quick Keys'

        if menuName in mw.customMenus:
            mw.customMenus[menuName].clear()

        for keyCombo, settings in self.settings['quickKeys'].items():
            menuText = 'Add Card [%s -> %s]' % (settings['modelName'],
                                                settings['extractDeck'])
            function = partial(mw.readingManager.textManager.extract, settings)
            addMenuItem(menuName, menuText, function, keyCombo)

        setMenuVisibility(menuName)
